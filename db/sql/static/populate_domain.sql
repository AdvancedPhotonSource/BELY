LOCK TABLES `domain` WRITE;
/*!40000 ALTER TABLE `domain` DISABLE KEYS */;
INSERT INTO `domain` VALUES
/*TODO remove all domains*/
(1, "Logbook", "Item domain to maintain logbooks.", NULL, "UID", 'System', NULL);
/*!40000 ALTER TABLE `domain` ENABLE KEYS */;
UNLOCK TABLES;
