-- Backup and restore db to repopulate the entity-types.
-- Execute by running `mysql BELY_DB_NAME --host=127.0.0.1 --user=logr -p < updateTo2024.1.sql`
-- 

ALTER TABLE entity_type ADD column `primary_template_item_id` int(11) unsigned NULL AFTER description;
ALTER TABLE entity_type ADD KEY `primary_template_item_entity_type_k1` (`primary_template_item_id`);
ALTER TABLE entity_type ADD CONSTRAINT `primary_template_item_entity_type_fk1` FOREIGN KEY (`primary_template_item_id`) REFERENCES `item` (`id`) ON UPDATE CASCADE;

delimiter //
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
	LIMIT limit_row;
END //

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
	LIMIT limit_row;
END //