LOCK TABLES `property_metadata` WRITE;
SET SESSION FOREIGN_KEY_CHECKS=0;
/*!40000 ALTER TABLE `property_metadata` DISABLE KEYS */;
INSERT INTO `property_metadata` VALUES
(1,1,'logLockout','0.0'),
(2,1,'docLockout','0.0'),
(3,1,'showTimestamps','true'),
(4,1,'logMode','copy'),
(5,2,'showTimestamps','true'),
(6,2,'docLockout','0.0'),
(7,2,'logMode','template per entry'),
(8,2,'logLockout','0.0'),
(9,3,'showTimestamps','true'),
(10,3,'logMode','copy'),
(11,3,'docLockout','0.0'),
(12,3,'logLockout','0.0');
/*!40000 ALTER TABLE `property_metadata` ENABLE KEYS */;
UNLOCK TABLES;
