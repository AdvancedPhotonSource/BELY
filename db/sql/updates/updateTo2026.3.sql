--
-- Table `notification_provider`
--

DROP TABLE IF EXISTS `notification_provider`;
CREATE TABLE `notification_provider` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(64) NOT NULL,
  `description` varchar(256) DEFAULT NULL,
  `instructions` TEXT DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `notification_provider_u1` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;

--
-- Table `notification_configuration`
--

DROP TABLE IF EXISTS `notification_configuration`;
CREATE TABLE `notification_configuration` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(64) NOT NULL,
  `description` varchar(256) DEFAULT NULL,
  `notification_provider_id` int(11) unsigned NOT NULL,
  `notification_endpoint` varchar(256) NOT NULL,
  `user_id` int(11) unsigned DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `notification_configuration_u1` (`name`),
  KEY `notification_configuration_k1` (`notification_provider_id`),
  KEY `notification_configuration_k2` (`user_id`),
  CONSTRAINT `notification_configuration_fk1` FOREIGN KEY (`notification_provider_id`) REFERENCES `notification_provider` (`id`) ON UPDATE CASCADE,
  CONSTRAINT `notification_configuration_fk2` FOREIGN KEY (`user_id`) REFERENCES `user_info` (`id`) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;

--
-- Table `notification_provider_config_key`
--

DROP TABLE IF EXISTS `notification_provider_config_key`;
CREATE TABLE `notification_provider_config_key` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `notification_provider_id` int(11) unsigned NOT NULL,
  `config_key` varchar(64) NOT NULL,
  `description` varchar(256) DEFAULT NULL,
  `is_required` bool NOT NULL DEFAULT 0,
  `display_order` int(11) DEFAULT 0,
  PRIMARY KEY (`id`),
  UNIQUE KEY `notification_provider_config_key_u1` (`notification_provider_id`, `config_key`),
  KEY `notification_provider_config_key_k1` (`notification_provider_id`),
  CONSTRAINT `notification_provider_config_key_fk1` FOREIGN KEY (`notification_provider_id`) REFERENCES `notification_provider` (`id`) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;

--
-- Table `notification_configuration_setting`
--

DROP TABLE IF EXISTS `notification_configuration_setting`;
CREATE TABLE `notification_configuration_setting` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `notification_configuration_id` int(11) unsigned NOT NULL,
  `notification_provider_config_key_id` int(11) unsigned NOT NULL,
  `config_value` varchar(256) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `notification_configuration_setting_u1` (`notification_configuration_id`, `notification_provider_config_key_id`),
  KEY `notification_configuration_setting_k1` (`notification_configuration_id`),
  KEY `notification_configuration_setting_k2` (`notification_provider_config_key_id`),
  CONSTRAINT `notification_configuration_setting_fk1` FOREIGN KEY (`notification_configuration_id`) REFERENCES `notification_configuration` (`id`) ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT `notification_configuration_setting_fk2` FOREIGN KEY (`notification_provider_config_key_id`) REFERENCES `notification_provider_config_key` (`id`) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;

-- ============================================================================
-- Notification Handler Configuration Tables
-- ============================================================================

-- Handler configuration key definitions
-- These define global handler settings like entry_updates, own_entry_edits
DROP TABLE IF EXISTS `notification_handler_config_key`;
CREATE TABLE `notification_handler_config_key` (
  `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT,
  `config_key` VARCHAR(64) NOT NULL COMMENT 'Key name like entry_updates',
  `display_name` VARCHAR(64) DEFAULT NULL COMMENT 'Short display name for UI',
  `description` VARCHAR(256) DEFAULT NULL,
  `value_type` ENUM('boolean', 'string', 'integer') NOT NULL DEFAULT 'boolean',
  `default_value` VARCHAR(256) DEFAULT NULL,
  `display_order` INT(11) DEFAULT 0,
  PRIMARY KEY (`id`),
  UNIQUE KEY `notification_handler_config_key_u1` (`config_key`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;

-- Per-configuration handler settings
-- Links notification_configuration to handler settings
DROP TABLE IF EXISTS `notification_configuration_handler_setting`;
CREATE TABLE `notification_configuration_handler_setting` (
  `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT,
  `notification_configuration_id` INT(11) UNSIGNED NOT NULL,
  `notification_handler_config_key_id` INT(11) UNSIGNED NOT NULL,
  `config_value` VARCHAR(256) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `notification_configuration_handler_setting_u1`
    (`notification_configuration_id`, `notification_handler_config_key_id`),
  KEY `notification_configuration_handler_setting_k1` (`notification_configuration_id`),
  KEY `notification_configuration_handler_setting_k2` (`notification_handler_config_key_id`),
  CONSTRAINT `notification_configuration_handler_setting_fk1`
    FOREIGN KEY (`notification_configuration_id`)
    REFERENCES `notification_configuration` (`id`)
    ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT `notification_configuration_handler_setting_fk2`
    FOREIGN KEY (`notification_handler_config_key_id`)
    REFERENCES `notification_handler_config_key` (`id`)
    ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;

-- ============================================================================
-- Initial Data Population
-- ============================================================================

--
-- Populate notification_provider
--

INSERT INTO `notification_provider` VALUES
(1,'apprise', 'Apprise unified notification library supporting email, Discord, Slack, Teams, etc.', '# Apprise Notification URLs

[Apprise](https://github.com/caronc/apprise) supports many notification services. Below are some common URL formats.

## Email (SMTP)

```
mailto://user@gmail.com
```

## Microsoft Teams

```
msteams://TokenA/TokenB/TokenC
```

## Slack

```
slack://TokenA/TokenB/TokenC/#channel
```

## Custom Webhooks

```
json://hostname/path
```

For the full list of supported services, see the [Apprise Wiki](https://github.com/caronc/apprise/wiki).');
--
-- Populate notification_handler_config_key
--

INSERT INTO `notification_handler_config_key` VALUES
(1,'entry_updates', 'Entry Updates', 'Notify document owner when log entries in their document are updated or deleted by others', 'boolean', 'true', 1),
(2,'entry_replies', 'Replies to My Entries', 'Notify original entry creator when someone replies to their log entry, or when replies are updated/deleted on their entry', 'boolean', 'true', 2),
(3,'new_entries', 'New Entries', 'Notify document owner when new log entries are created in their document (excluding entries they create themselves)', 'boolean', 'true', 3),
(4,'document_replies', 'All Document Replies', 'Notify document owner when replies are added, updated, or deleted anywhere in their document', 'boolean', 'true', 4),
(5,'reactions', 'Entry Reactions', 'Notify entry creator when someone adds or removes a reaction (like emoji) to their entry', 'boolean', 'true', 5),
(6,'own_entry_edits', 'Edits to My Entries', 'Notify users when their own entries (or replies they created) are edited or deleted by someone else', 'boolean', 'true', 6);

-- ============================================================================
-- Update search stored procedures for word-order-independent search
-- ============================================================================

delimiter //

DROP PROCEDURE IF EXISTS search_items_no_parent;//
CREATE PROCEDURE `search_items_no_parent` (
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
	SET @select_stmt = "SELECT DISTINCT item.* from item ";
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

	-- Split search_string into words and require each word to match at least one field
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
			SET @word_like = CONCAT('"%', @word, '%"');
			SET @where_stmt = CONCAT(@where_stmt,
				'AND (',
				'item.name LIKE ', @word_like, ' ',
				'OR item.qr_id LIKE ', @word_like, ' ',
				'OR item.item_identifier1 LIKE ', @word_like, ' ',
				'OR item.item_identifier2 LIKE ', @word_like, ' ',
				'OR ie.description LIKE ', @word_like, ' ',
				'OR derived_item.name LIKE ', @word_like, ' ',
				'OR owneru.username LIKE ', @word_like, ' ',
				'OR creatoru.username LIKE ', @word_like, ' ',
				'OR updateu.username LIKE ', @word_like, ' ',
				') ');
		END IF;
	END WHILE;

	IF user_id_list THEN
		SET @where_stmt = CONCAT(@where_stmt,
		"AND (",
		"FIND_IN_SET(owneru.id, '", user_id_list, "')",
		"OR FIND_IN_SET(creatoru.id, '", user_id_list, "')",
		"OR FIND_IN_SET(updateu.id, '", user_id_list, "')",
		")");
	END IF;

	IF entity_type_id_list THEN
		SET @from_stmt = CONCAT(@from_stmt, "
			INNER JOIN item_entity_type iet on item.id = iet.item_id");
		SET @where_stmt = CONCAT(@where_stmt, "
			AND FIND_IN_SET(iet.entity_type_id, '", entity_type_id_list, "') ");
	END IF;

	IF item_type_id_list THEN
		SET @from_stmt = CONCAT(@from_stmt, "
			INNER JOIN item_item_type iit on item.id = iit.item_id ");
		set @where_stmt = CONCAT(@where_stmt, "
			AND FIND_IN_SET(iit.item_type_id, '", item_type_id_list, "') ");
	END IF;

	IF start_modified_time THEN
		SET @where_stmt = CONCAT(@where_stmt, "
			AND ei.last_modified_on_date_time > '", start_modified_time, "' ");
	END IF;

	IF end_modified_time THEN
		SET @where_stmt = CONCAT(@where_stmt, "
			AND ei.last_modified_on_date_time < '", end_modified_time, "' ");
	END IF;

	IF start_created_time THEN
		SET @where_stmt = CONCAT(@where_stmt, "
			AND ei.created_on_date_time > '", start_created_time, "' ");
	END IF;

	IF end_created_time THEN
		SET @where_stmt = CONCAT(@where_stmt, "
			AND ei.created_on_date_time < '", end_created_time, "' ");
	END IF;


	SET @from_stmt = CONCAT(@from_stmt, "
		LEFT OUTER JOIN item derived_item ON derived_item.id = item.derived_from_item_id
		LEFT OUTER JOIN v_item_hierarchy vih on vih.child_item_id = item.id
	");

	SET @sql_stmt = CONCAT(@select_stmt, @from_stmt, @where_stmt, "
		ORDER BY ei.last_modified_on_date_time DESC
		LIMIT ", limit_row);

	prepare stmt from @sql_stmt;
	execute stmt;
	deallocate prepare stmt;

END //

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
	SET @select_stmt = "SELECT DISTINCT parent_item.*, log.*, log.id as log_id ";
	SET @from_stmt = "FROM item
	INNER JOIN v_item_self_element ise ON item.id = ise.item_id
	INNER JOIN item_element ie ON ise.self_element_id = ie.id
	LEFT OUTER JOIN item_element_log iel on iel.item_element_id = ie.id
	LEFT OUTER JOIN v_item_hierarchy cih on cih.child_item_id = item.id";
	SET @from_tbls = ", item as parent_item, log";

	SET @where_stmt = "WHERE ";
	SET @where_stmt = CONCAT(@where_stmt, 'item.domain_id = ', domain_id, ' ');

	SET @where_stmt = CONCAT(@where_stmt, "AND (log.id = iel.log_id or log.parent_log_id = iel.log_id) ");

	SET @where_stmt = CONCAT(@where_stmt, "AND (
		parent_item.id = cih.parent_item_id
		OR
		(cih.parent_item_id IS NULL AND
		parent_item.id = item.id
		)) ");

	-- Split search_string into words and require each word to match log text
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
			SET @where_stmt = CONCAT(@where_stmt, 'AND (log.text LIKE "%', @word, '%") ');
		END IF;
	END WHILE;

	IF user_id_list THEN
		SET @where_stmt = CONCAT(@where_stmt,
		"AND (",
		"FIND_IN_SET(log.entered_by_user_id, '", user_id_list, "')",
		"OR FIND_IN_SET(log.last_modified_by_user_id, '", user_id_list, "')",
		")");
	END IF;

	IF item_type_id_list THEN
		SET @from_tbls = CONCAT(@from_tbls, ", item_item_type iit");
		set @where_stmt = CONCAT(@where_stmt, "
			AND parent_item.id = iit.item_id
			AND FIND_IN_SET(iit.item_type_id, '", item_type_id_list, "') ");
	END IF;

	IF entity_type_id_list THEN
		SET @from_tbls = CONCAT(@from_tbls, ", item_entity_type as iet");
		SET @where_stmt = CONCAT(@where_stmt, "
			AND parent_item.id = iet.item_id
			AND FIND_IN_SET(iet.entity_type_id, '", entity_type_id_list, "') ");
	END IF;

	IF start_modified_time THEN
		SET @where_stmt = CONCAT(@where_stmt, "
			AND log.last_modified_on_date_time > '", start_modified_time, "' ");
	END IF;

	IF end_modified_time THEN
		SET @where_stmt = CONCAT(@where_stmt, "
			AND log.last_modified_on_date_time < '", end_modified_time, "' ");
	END IF;

	IF start_created_time THEN
		SET @where_stmt = CONCAT(@where_stmt, "
			AND log.entered_on_date_time > '", start_created_time, "' ");
	END IF;

	IF end_created_time THEN
		SET @where_stmt = CONCAT(@where_stmt, "
			AND log.entered_on_date_time < '", end_created_time, "' ");
	END IF;

	SET @from_stmt = CONCAT(@from_stmt, @from_tbls, " ");

	SET @sql_stmt = CONCAT(@select_stmt, @from_stmt, @where_stmt, "
		ORDER BY log.last_modified_on_date_time DESC
		LIMIT ", limit_row);

	prepare stmt from @sql_stmt;
	execute stmt;
	deallocate prepare stmt;
END //

delimiter ;