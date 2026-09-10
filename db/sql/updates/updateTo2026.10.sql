-- Execute by running `mysql BELY_DB_NAME --host=127.0.0.1 --user=logr -p < updateTo2026.10.sql`

--
-- Default owner user group per logbook type (entity_type)
--

ALTER TABLE entity_type ADD column `default_owner_user_group_id` int(11) unsigned DEFAULT NULL AFTER primary_template_item_id;
ALTER TABLE entity_type ADD KEY `default_owner_user_group_entity_type_k3` (`default_owner_user_group_id`);
ALTER TABLE entity_type ADD CONSTRAINT `default_owner_user_group_entity_type_fk3` FOREIGN KEY (`default_owner_user_group_id`) REFERENCES `user_group` (`id`) ON UPDATE CASCADE ON DELETE SET NULL;
