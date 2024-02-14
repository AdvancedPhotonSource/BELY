ALTER TABLE entity_type ADD column `sort_order` float(10,2) unsigned DEFAULT NULL AFTER primary_template_item_id;
ALTER TABLE entity_type ADD column `display_name` varchar(128) DEFAULT NULL AFTER name; 
ALTER TABLE entity_type ADD column `long_display_name` varchar(256) DEFAULT NULL AFTER display_name; 
ALTER TABLE entity_type ADD column `custom_list_url` varchar(64) DEFAULT NULL AFTER description; 
ALTER TABLE entity_type ADD column `parent_entity_type_id` int(11) unsigned NULL AFTER custom_list_url;
ALTER TABLE entity_type ADD KEY `parent_entity_type_id_k2` (`parent_entity_type_id`);
ALTER TABLE entity_type ADD CONSTRAINT `parent_entity_type_id_fk2` FOREIGN KEY (`parent_entity_type_id`) REFERENCES `entity_type` (`id`) ON UPDATE CASCADE;
ALTER TABLE entity_type ADD column `is_internal` bool NOT NULL DEFAULT 0 AFTER sort_order; 

-- TODO update 
-- (1,'Template'),
-- (2,'aop'),
-- (3,'ctl'),
-- (4,'ops'),
-- (5,'sandbox') ,  
-- Columns: id name display_name long_display_name description custom_list_url parent_entity_type_id primary_template_item_id sort_order is_internal
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
