-- Backup and restore db to repopulate the entity-types. 

ALTER TABLE entity_type ADD column `primary_template_item_id` int(11) unsigned NULL AFTER description;
ALTER TABLE entity_type ADD KEY `primary_template_item_entity_type_k1` (`primary_template_item_id`);
ALTER TABLE entity_type ADD CONSTRAINT `primary_template_item_entity_type_fk1` FOREIGN KEY (`primary_template_item_id`) REFERENCES `item` (`id`) ON UPDATE CASCADE;