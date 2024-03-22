CREATE TABLE `user_session` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `user_id` int(11) unsigned NOT NULL,
  `session_name` varchar(128) DEFAULT NULL,
  `expiration_date_time` datetime NOT NULL,
  `session_key` varchar(256) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `user_session_k1` (`user_id`),
  CONSTRAINT `user_session_fk1` FOREIGN KEY (`user_id`) REFERENCES `user_info` (`id`) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;


delimiter //

DROP PROCEDURE IF EXISTS cleanup_sessions;//
CREATE PROCEDURE `cleanup_sessions` () 
BEGIN
	DELETE FROM user_session WHERE expiration_date_time < CURRENT_TIMESTAMP();
END //

-- Ensure that event_scheduler is on
-- https://mariadb.com/docs/server/ref/mdb/system-variables/event_scheduler/
DROP EVENT IF EXISTS session_clean_event;//
CREATE EVENT session_clean_event 
ON SCHEDULE EVERY 1 HOUR STARTS CURRENT_TIMESTAMP
DO
  CALL cleanup_sessions(); // 

-- Run as db admin to start during runtime. 
-- SET GLOBAL event_scheduler=ON;

DROP PROCEDURE IF EXISTS search_items_no_parent;//
CREATE PROCEDURE `search_items_no_parent` (IN limit_row int, IN domain_id int, IN entity_type_id INT, IN item_type_id int, IN start_time datetime, IN end_time datetime, IN search_string VARCHAR(255)) 
BEGIN
	SET search_string = CONCAT('"%', search_string, '%"'); 

	SET @select_stmt = "SELECT item.* from item ";
	SET @from_stmt = "
	INNER JOIN v_item_self_element ise ON item.id = ise.item_id 
	INNER JOIN item_element ie ON ise.self_element_id = ie.id
	INNER JOIN entity_info ei ON ise.entity_info_id = ei.id
	INNER JOIN user_info owneru ON ei.owner_user_id = owneru.id
	INNER JOIN user_info creatoru ON ei.created_by_user_id = creatoru.id
	INNER JOIN user_info updateu ON ei.last_modified_by_user_id = updateu.id
	"; 

	SET @where_stmt = "WHERE "; 
	SET @where_stmt = CONCAT(@where_stmt, "item.domain_id = ", domain_id, " "); 
	SET @where_stmt = CONCAT(@where_stmt, "AND vih.parent_item_id IS NULL "); 

	SET @where_stmt = CONCAT(@where_stmt, "AND (",
	"item.name LIKE ", search_string, " ",
	"OR item.qr_id LIKE ", search_string, " ",
	"OR item.item_identifier1 LIKE ", search_string, " ",
	"OR item.item_identifier2 LIKE ", search_string, " ",
	"OR ie.description LIKE ", search_string, " ",
	"OR derived_item.name LIKE ", search_string, " ",
	"OR owneru.username LIKE ", search_string, " ",
	"OR creatoru.username LIKE ", search_string, " ",
	"OR updateu.username LIKE ", search_string, " ",
	") ");

	IF entity_type_id THEN			
		SET @from_stmt = CONCAT(@from_stmt, "
			INNER JOIN item_entity_type iet on item.id = iet.item_id
			INNER JOIN entity_type et on iet.entity_type_id = et.id "); 
		SET @where_stmt = CONCAT(@where_stmt, "
			AND (iet.entity_type_id = ", entity_type_id, "
			OR et.parent_entity_type_id = ", entity_type_id, ") ");
	END IF;

	IF item_type_id THEN 
		SET @from_stmt = CONCAT(@from_stmt, "
			INNER JOIN item_item_type iit on item.id = iit.item_id ");
		set @where_stmt = CONCAT(@where_stmt, "
			AND iit.item_type_id = ", item_type_id, " ");
	END IF; 

	IF start_time THEN
		SET @where_stmt = CONCAT(@where_stmt, "
			AND ei.last_modified_on_date_time > '", start_time, "' ");
	END IF;

	IF end_time THEN
		SET @where_stmt = CONCAT(@where_stmt, "
			AND ei.last_modified_on_date_time < '", end_time, "' ");			
	END IF;


	SET @from_stmt = CONCAT(@from_stmt, "
		LEFT OUTER JOIN item derived_item ON derived_item.id = item.derived_from_item_id 
		LEFT OUTER JOIN v_item_hierarchy vih on vih.child_item_id = item.id
	");

	SET @sql_stmt = CONCAT(@select_stmt, @from_stmt, @where_stmt, "
		ORDER BY item.id DESC 
		LIMIT ", limit_row);

	prepare stmt from @sql_stmt; 
	execute stmt;
	deallocate prepare stmt;

END //

DROP PROCEDURE IF EXISTS search_item_logs;//
CREATE PROCEDURE `search_item_logs` (IN limit_row int, IN domain_id int, IN entity_type_id INT, IN item_type_id int, IN start_time datetime, IN end_time datetime, IN search_string VARCHAR(255)) 
BEGIN
	SET search_string = CONCAT('%', search_string, '%'); 

	SET @select_stmt = "SELECT parent_item.*, log.*, log.id as log_id ";
	SET @from_stmt = "FROM item 
	INNER JOIN v_item_self_element ise ON item.id = ise.item_id 
	INNER JOIN item_element ie ON ise.self_element_id = ie.id
	LEFT OUTER JOIN item_element_log iel on iel.item_element_id = ie.id
	INNER JOIN log on log.id = iel.log_id "; 

	SET @where_stmt = "WHERE ";
	SET @where_stmt = CONCAT(@where_stmt, 'item.domain_id = ', domain_id, ' '); 
	SET @where_stmt = CONCAT(@where_stmt, "AND (
		parent_item.id = cih.parent_item_id 
		OR
		(cih.parent_item_id IS NULL AND 
		parent_item.id = item.id
		)) "); 

	SET @where_stmt = CONCAT(@where_stmt, 'AND (log.text LIKE "', search_string, '") '); 

	IF item_type_id THEN 
		SET @from_stmt = CONCAT(@from_stmt, "
			INNER JOIN item_item_type iit on item.id = iit.item_id ");
		set @where_stmt = CONCAT(@where_stmt, "
			AND iit.item_type_id = ", item_type_id, " ");
	END IF; 

	IF entity_type_id THEN			
		SET @from_stmt = CONCAT(@from_stmt, "
			INNER JOIN item_entity_type iet on item.id = iet.item_id
			INNER JOIN entity_type et on iet.entity_type_id = et.id "); 
		SET @where_stmt = CONCAT(@where_stmt, "
			AND (iet.entity_type_id = ", entity_type_id, "
			OR et.parent_entity_type_id = ", entity_type_id, ") ");
	END IF;
	
	IF start_time THEN
		SET @where_stmt = CONCAT(@where_stmt, "
			AND log.last_modified_on_date_time > '", start_time, "' ");
	END IF;

	IF end_time THEN
		SET @where_stmt = CONCAT(@where_stmt, "
			AND log.last_modified_on_date_time < '", end_time, "' ");			
	END IF;

	SET @from_stmt = CONCAT(@from_stmt, "
		LEFT OUTER JOIN v_item_hierarchy cih on cih.child_item_id = item.id,
		item as parent_item "); 
		
	SET @sql_stmt = CONCAT(@select_stmt, @from_stmt, @where_stmt, "
		ORDER BY parent_item.id DESC 
		LIMIT ", limit_row);

	prepare stmt from @sql_stmt; 
	execute stmt;
	deallocate prepare stmt;	
END //