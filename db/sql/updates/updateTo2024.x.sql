ALTER TABLE entity_type ADD column `sort_order` float(10,2) unsigned DEFAULT NULL AFTER primary_template_item_id;
ALTER TABLE entity_type ADD column `display_name` varchar(128) DEFAULT NULL AFTER name; 
ALTER TABLE entity_type ADD column `long_display_name` varchar(256) DEFAULT NULL AFTER display_name; 
ALTER TABLE entity_type ADD column `custom_list_url` varchar(64) DEFAULT NULL AFTER description; 
ALTER TABLE entity_type ADD column `parent_entity_type_id` int(11) unsigned NULL AFTER custom_list_url;
ALTER TABLE entity_type ADD KEY `parent_entity_type_id_k2` (`parent_entity_type_id`);
ALTER TABLE entity_type ADD CONSTRAINT `parent_entity_type_id_fk2` FOREIGN KEY (`parent_entity_type_id`) REFERENCES `entity_type` (`id`) ON UPDATE CASCADE;
ALTER TABLE entity_type ADD column `is_internal` bool NOT NULL DEFAULT 0 AFTER sort_order; 

ALTER TABLE log ADD column `last_modified_on_date_time` datetime NOT NULL AFTER `entered_on_date_time`; 
ALTER TABLE log ADD column `last_modified_by_user_id` int(11) unsigned NOT NULL AFTER `last_modified_on_date_time`;  
ALTER TABLE log ADD KEY `log_k3` (`last_modified_by_user_id`);
-- Copy over the entered and modified user and date. 
update log set last_modified_on_date_time = entered_on_date_time;
update log set last_modified_by_user_id  = entered_by_user_id;
ALTER TABLE log ADD CONSTRAINT `log_fk3` FOREIGN KEY (`last_modified_by_user_id`) REFERENCES `user_info` (`id`) ON UPDATE CASCADE; 

INSERT INTO `setting_type` VALUES
(16,'ItemDomainLogbook.Home.EntityTypeId1','1st entityType Id to show up on the home page.',''),
(17,'ItemDomainLogbook.Home.EntityTypeId2','2nd entityType Id to show up on the home page.',''),
(18,'ItemDomainLogbook.Home.EntityTypeId3','3rd entityType Id to show up on the home page.','');

-- Prepare entity_type changes for next version. 
UPDATE entity_type SET is_internal = 1, display_name="Template" WHERE id=1;
UPDATE entity_type SET name='studies', display_name = "Machine Studies", sort_order = 1.0 WHERE id = 2; 
UPDATE entity_type SET name='maintanance', display_name = "Maintanance", sort_order = 2.0 WHERE id = 3; 
UPDATE entity_type SET display_name = "Operations", sort_order = 3.0, custom_list_url = 'opsList' WHERE id = 4; 
UPDATE entity_type SET display_name = "Sandbox", sort_order = 999.0 WHERE id = 5; 

-- Move CTL records to new log document 
INSERT INTO entity_type VALUE (6, "ctl", "Controls", NULL, "", NULL, 3, NULL, NULL, 0); 
INSERT INTO allowed_entity_type_domain VALUE (1, 6);
UPDATE item_entity_type set entity_type_id = 6 where entity_type_id = 3;

-- Move machine studies records to new log document 
INSERT INTO entity_type VALUE (7, "studies-sr", "SR", "SR Studies", "", NULL, 2, NULL, NULL, 0); 
INSERT INTO allowed_entity_type_domain VALUE (1, 7);
UPDATE item_entity_type set entity_type_id = 7 where entity_type_id = 2;

ALTER TABLE entity_type MODIFY display_name varchar(128) NOT NULL;

ALTER TABLE entity_type MODIFY is_internal bool NOT NULL DEFAULT 0;

delimiter //

DROP PROCEDURE IF EXISTS search_items_no_parent;//
CREATE PROCEDURE `search_items_no_parent` (IN limit_row int, IN domain_id int, IN search_string VARCHAR(255)) 
BEGIN
	SET search_string = CONCAT('%', search_string, '%'); 
	SELECT item.* from item 
	INNER JOIN v_item_self_element ise ON item.id = ise.item_id 
	INNER JOIN item_element ie ON ise.self_element_id = ie.id
	INNER JOIN entity_info ei ON ise.entity_info_id = ei.id
	INNER JOIN user_info owneru ON ei.owner_user_id = owneru.id
	INNER JOIN user_info creatoru ON ei.created_by_user_id = creatoru.id
	INNER JOIN user_info updateu ON ei.last_modified_by_user_id = updateu.id
	LEFT OUTER JOIN item derived_item ON derived_item.id = item.derived_from_item_id 
	LEFT OUTER JOIN v_item_hierarchy vih on vih.child_item_id = item.id
	WHERE item.domain_id = domain_id
	AND vih.parent_item_id IS NULL
	AND (
		item.name LIKE search_string
		OR item.qr_id LIKE search_string
		OR item.item_identifier1 LIKE search_string
		OR item.item_identifier2 LIKE search_string
		OR ie.description LIKE search_string
		OR derived_item.name LIKE search_string
		OR owneru.username LIKE search_string
		OR creatoru.username LIKE search_string
		OR updateu.username LIKE search_string
	)
	ORDER BY item.id DESC
	LIMIT limit_row;
END //

DROP PROCEDURE IF EXISTS search_item_logs;//
CREATE PROCEDURE `search_item_logs` (IN limit_row int, IN domain_id int, IN search_string VARCHAR(255)) 
BEGIN
	SET search_string = CONCAT('%', search_string, '%'); 
	
	SELECT parent_item.*, log.*, log.id as log_id from item 
	INNER JOIN v_item_self_element ise ON item.id = ise.item_id 
	INNER JOIN item_element ie ON ise.self_element_id = ie.id
	LEFT OUTER JOIN item_element_log iel on iel.item_element_id = ie.id
	INNER JOIN log on log.id = iel.log_id
	LEFT OUTER JOIN v_item_hierarchy cih on cih.child_item_id = item.id,
	item as parent_item
	WHERE item.domain_id = domain_id	
	AND (
		log.text LIKE search_string
	)
	AND (
		parent_item.id = cih.parent_item_id 
		OR
		(cih.parent_item_id IS NULL AND 
		parent_item.id = item.id
		)
	) 
	ORDER BY parent_item.id DESC
	LIMIT limit_row;
END //