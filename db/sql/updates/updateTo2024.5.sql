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
	SET search_string = CONCAT('"%', search_string, '%"'); 

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
	SET search_string = CONCAT('%', search_string, '%'); 

	SET @select_stmt = "SELECT DISTINCT parent_item.*, log.*, log.id as log_id ";
	SET @from_stmt = "FROM item 
	INNER JOIN v_item_self_element ise ON item.id = ise.item_id 
	INNER JOIN item_element ie ON ise.self_element_id = ie.id
	LEFT OUTER JOIN item_element_log iel on iel.item_element_id = ie.id
	INNER JOIN log on log.id = iel.log_id 
	LEFT OUTER JOIN v_item_hierarchy cih on cih.child_item_id = item.id"; 

	SET @from_tbls = ", item as parent_item "; 

	SET @where_stmt = "WHERE ";
	SET @where_stmt = CONCAT(@where_stmt, 'item.domain_id = ', domain_id, ' '); 
	SET @where_stmt = CONCAT(@where_stmt, "AND (
		parent_item.id = cih.parent_item_id 
		OR
		(cih.parent_item_id IS NULL AND 
		parent_item.id = item.id
		)) "); 

	SET @where_stmt = CONCAT(@where_stmt, 'AND (log.text LIKE "', search_string, '") '); 

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