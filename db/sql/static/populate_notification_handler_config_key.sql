LOCK TABLES `notification_handler_config_key` WRITE;
/*!40000 ALTER TABLE `notification_handler_config_key` DISABLE KEYS */;
INSERT INTO `notification_handler_config_key` VALUES
(1,'entry_updates', 'Entry Updates', 'Notify document owner when log entries in their document are updated or deleted by others', 'boolean', 'true', 1),
(2,'entry_replies', 'Replies to My Entries', 'Notify original entry creator when someone replies to their log entry, or when replies are updated/deleted on their entry', 'boolean', 'true', 2),
(3,'new_entries', 'New Entries', 'Notify document owner when new log entries are created in their document (excluding entries they create themselves)', 'boolean', 'true', 3),
(4,'document_replies', 'All Document Replies', 'Notify document owner when replies are added, updated, or deleted anywhere in their document', 'boolean', 'true', 4),
(5,'reactions', 'Entry Reactions', 'Notify entry creator when someone adds or removes a reaction (like emoji) to their entry', 'boolean', 'true', 5),
(6,'own_entry_edits', 'Edits to My Entries', 'Notify users when their own entries (or replies they created) are edited or deleted by someone else', 'boolean', 'true', 6);
/*!40000 ALTER TABLE `notification_handler_config_key` ENABLE KEYS */;
UNLOCK TABLES;
