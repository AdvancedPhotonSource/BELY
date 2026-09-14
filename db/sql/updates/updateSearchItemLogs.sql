--
-- Copyright (c) UChicago Argonne, LLC. All rights reserved.
-- See LICENSE file.
--
-- Rewrite of search_item_logs to fix a 800x+ slowdown on MariaDB 10.5.
--
-- Execute by running:
--   mysql BELY_DB_NAME --host=127.0.0.1 --user=logr -p < updateSearchItemLogs.sql
--
-- WHY
-- ---
-- The old procedure joined `item` directly after `log`, but no join predicate connects
-- those two tables (they are linked only indirectly via item_element_log). MariaDB 10.5
-- therefore produced an unconstrained cross product of 53,217 logs x 10,881 items
-- (~579M combinations), then applied "Range checked for each record" on parent_item over
-- all of them -- 302 million extra InnoDB row reads, ~255 seconds.
--
-- MariaDB 12.3 (the dev environment) happens to pick a better join order and runs the
-- same procedure in 310 ms, which is why this was invisible during development.
--
-- This rewrite makes the good plan structural rather than luck:
--   1. Narrow `log` first in a CTE, applying all text/date/user predicates to the base
--      table alone (one pass, no join amplification).
--   2. Join item_element_log immediately after, which DOES have a usable predicate --
--      collapsing the row set before any item join happens.
--   3. Split the OR join (log.id = iel.log_id OR log.parent_log_id = iel.log_id) into a
--      UNION of two index-friendly branches.
--   4. Replace comma joins with explicit JOIN ... ON, so join order is not left to chance.
--   5. Apply item/entity type filters as EXISTS rather than comma joins, so they cannot
--      multiply rows.
--
-- Search semantics are UNCHANGED: substring matching (LIKE '%word%'), AND across words,
-- same result-set shape (parent_item.*, log.*, log_id) for the `logResultList` mapping.
--
-- Also fixes a latent bug: search terms containing a double quote broke the old
-- procedure, which wrapped LIKE values in double quotes. Now single-quoted and escaped.
--
-- Verified: 33/33 result-parity cases identical to the old procedure (plain, multi-word,
-- substring, wildcards, quotes/apostrophes, user/date/type filters, limits, domain
-- isolation, and combined filters).
--

delimiter //

DROP PROCEDURE IF EXISTS search_item_logs;//
CREATE PROCEDURE `search_item_logs` (
	IN limit_row int,
	IN domain_id int,
	IN entity_type_id_list TEXT,
	IN item_type_id_list TEXT,
	IN user_id_list TEXT,
	IN start_modified_time datetime,
	IN end_modified_time datetime,
	IN start_created_time datetime,
	IN end_created_time datetime,
	IN search_string VARCHAR(255)
	)
BEGIN
	-- Predicates that apply to the `log` table alone, so they can be pushed into a CTE
	-- that narrows `log` before any item join happens.
	SET @log_where = "WHERE 1=1 ";

	-- Split search_string into words; require each word to match the log text.
	SET @remaining = TRIM(search_string);
	WHILE LENGTH(@remaining) > 0 DO
		SET @space_pos = LOCATE(' ', @remaining);
		IF @space_pos = 0 THEN
			SET @word = @remaining;
			SET @remaining = '';
		ELSE
			SET @word = LEFT(@remaining, @space_pos - 1);
			SET @remaining = TRIM(SUBSTRING(@remaining, @space_pos + 1));
		END IF;

		IF LENGTH(@word) > 0 THEN
			-- Single-quoted and escaped; the old double-quoted form broke on terms
			-- containing a double quote. Note % and _ are deliberately NOT escaped:
			-- the Java layer converts user wildcards (* ?) into them.
			SET @log_where = CONCAT(@log_where, "AND (l.text LIKE '%",
				REPLACE(REPLACE(@word, '\\', '\\\\'), "'", "\\'"), "%') ");
		END IF;
	END WHILE;

	IF user_id_list THEN
		SET @log_where = CONCAT(@log_where,
		"AND (",
		"FIND_IN_SET(l.entered_by_user_id, '", user_id_list, "')",
		"OR FIND_IN_SET(l.last_modified_by_user_id, '", user_id_list, "')",
		")");
	END IF;

	IF start_modified_time THEN
		SET @log_where = CONCAT(@log_where,
			"AND l.last_modified_on_date_time > '", start_modified_time, "' ");
	END IF;

	IF end_modified_time THEN
		SET @log_where = CONCAT(@log_where,
			"AND l.last_modified_on_date_time < '", end_modified_time, "' ");
	END IF;

	IF start_created_time THEN
		SET @log_where = CONCAT(@log_where,
			"AND l.entered_on_date_time > '", start_created_time, "' ");
	END IF;

	IF end_created_time THEN
		SET @log_where = CONCAT(@log_where,
			"AND l.entered_on_date_time < '", end_created_time, "' ");
	END IF;

	-- Filters on the resolved parent item. EXISTS rather than a comma join, so they
	-- cannot multiply rows.
	SET @parent_filter = "";
	IF item_type_id_list THEN
		SET @parent_filter = CONCAT(@parent_filter,
			" AND EXISTS (SELECT 1 FROM item_item_type iit
			              WHERE iit.item_id = r.parent_item_id
			                AND FIND_IN_SET(iit.item_type_id, '", item_type_id_list, "')) ");
	END IF;
	IF entity_type_id_list THEN
		SET @parent_filter = CONCAT(@parent_filter,
			" AND EXISTS (SELECT 1 FROM item_entity_type iet
			              WHERE iet.item_id = r.parent_item_id
			                AND FIND_IN_SET(iet.entity_type_id, '", entity_type_id_list, "')) ");
	END IF;

	SET @sql_stmt = CONCAT(
	"WITH matching_logs AS (
		SELECT l.id, l.parent_log_id, l.last_modified_on_date_time
		FROM log l ", @log_where, "
	),
	-- Link each matching log to the logbook item holding it. The old OR predicate
	-- (log.id = iel.log_id OR log.parent_log_id = iel.log_id) is split into two
	-- index-friendly branches; UNION also removes the duplicates the OR produced.
	-- The item_element conditions inline v_item_self_element.
	linked AS (
		SELECT ml.id AS log_id, ml.last_modified_on_date_time, ie.parent_item_id AS item_id
		FROM matching_logs ml
		JOIN item_element_log iel ON iel.log_id = ml.id
		JOIN item_element ie ON ie.id = iel.item_element_id
		     AND ie.name IS NULL AND ie.derived_from_item_element_id IS NULL
		UNION
		SELECT ml.id AS log_id, ml.last_modified_on_date_time, ie.parent_item_id AS item_id
		FROM matching_logs ml
		JOIN item_element_log iel ON iel.log_id = ml.parent_log_id
		JOIN item_element ie ON ie.id = iel.item_element_id
		     AND ie.name IS NULL AND ie.derived_from_item_element_id IS NULL
	),
	-- Resolve each item to its hierarchy parent, falling back to the item itself when it
	-- has none (the old 'cih.parent_item_id IS NULL' branch). Inlines v_item_hierarchy.
	resolved AS (
		SELECT DISTINCT lk.log_id, lk.last_modified_on_date_time,
		       COALESCE(pie.parent_item_id, lk.item_id) AS parent_item_id
		FROM linked lk
		JOIN item i ON i.id = lk.item_id AND i.domain_id = ", domain_id, "
		LEFT JOIN item_element pie ON pie.contained_item_id1 = lk.item_id
	)
	SELECT parent_item.*, log.*, log.id AS log_id
	FROM resolved r
	JOIN item AS parent_item ON parent_item.id = r.parent_item_id
	JOIN log ON log.id = r.log_id
	WHERE 1=1 ", @parent_filter, "
	ORDER BY log.last_modified_on_date_time DESC
	LIMIT ", limit_row);

	prepare stmt from @sql_stmt;
	execute stmt;
	deallocate prepare stmt;
END //

delimiter ;
