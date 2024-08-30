LOCK TABLES `property_type` WRITE;
SET SESSION FOREIGN_KEY_CHECKS=0;
/*!40000 ALTER TABLE `property_type` DISABLE KEYS */;
INSERT INTO `property_type` VALUES
(1,'Image',NULL,NULL,1,2,NULL,NULL,0,0,0,1,1),
(2,'Document (Upload)','',NULL,1,1,'','',0,0,0,1,1),
(3,'Logbook Document Settings',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL,NULL);
/*!40000 ALTER TABLE `property_type` ENABLE KEYS */;
UNLOCK TABLES;
