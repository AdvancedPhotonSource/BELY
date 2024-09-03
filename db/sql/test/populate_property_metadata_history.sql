LOCK TABLES `property_metadata_history` WRITE;
SET SESSION FOREIGN_KEY_CHECKS=0;
/*!40000 ALTER TABLE `property_metadata_history` DISABLE KEYS */;
INSERT INTO `property_metadata_history` VALUES
(1,1,'docLockout','0.0'),
(2,1,'logMode','none'),
(3,1,'logLockout','0.0'),
(4,1,'showTimestamps','true');
/*!40000 ALTER TABLE `property_metadata_history` ENABLE KEYS */;
UNLOCK TABLES;
