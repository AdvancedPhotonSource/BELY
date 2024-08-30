LOCK TABLES `log` WRITE;
SET SESSION FOREIGN_KEY_CHECKS=0;
/*!40000 ALTER TABLE `log` DISABLE KEYS */;
INSERT INTO `log` VALUES
(10,'Sample Init Log','2024-08-23 09:19:40','2024-08-23 09:19:40',1,1,'2024-08-23 09:19:40',NULL,NULL,NULL),
(13,'Per Entry Log','2024-08-23 09:20:17','2024-08-23 09:20:17',1,1,'2024-08-23 09:20:17',NULL,NULL,NULL),
(14,'Another test entry','2024-08-29 14:46:20','2024-08-29 14:46:20',1,1,'2024-08-29 14:46:20',NULL,NULL,NULL),
(15,'A third one as well','2024-08-29 14:46:27','2024-08-29 14:46:27',1,1,'2024-08-29 14:46:27',NULL,NULL,NULL),
(16,'How \r\n\r\nAbout \r\n\r\nMultiple \r\n\r\nLines','2024-08-29 14:46:40','2024-08-29 14:46:40',1,1,'2024-08-29 14:46:40',NULL,NULL,NULL),
(17,'User: logr | Created: Test Template Sections [Item Id: 78]','2024-08-29 14:47:22','2024-08-29 14:47:22',1,1,NULL,NULL,NULL,NULL),
(18,'User: logr | Updated: Test Template Sections [Item Id: 78]','2024-08-29 14:47:33','2024-08-29 14:47:33',1,1,NULL,NULL,NULL,NULL),
(19,'Section 1 Entry','2024-08-29 14:47:34','2024-08-29 14:47:34',1,1,'2024-08-29 14:47:34',NULL,NULL,NULL),
(20,'User: logr | Updated: Test Template Sections [Item Id: 78]','2024-08-29 14:47:50','2024-08-29 14:47:50',1,1,NULL,NULL,NULL,NULL),
(21,'User: logr | Updated: Test Template Sections [Item Id: 78]','2024-08-29 14:48:01','2024-08-29 14:48:01',1,1,NULL,NULL,NULL,NULL),
(22,'Section 3 Entry','2024-08-29 14:48:09','2024-08-29 14:48:09',1,1,'2024-08-29 14:48:09',NULL,NULL,NULL),
(23,'User: logr | Updated: Test Template Sections + Copy [Item Id: 78]','2024-08-29 14:48:30','2024-08-29 14:48:30',1,1,NULL,NULL,NULL,NULL),
(24,'User: logr | Updated: Test Template Sections + Copy [Item Id: 78]','2024-08-29 14:48:30','2024-08-29 14:48:30',1,1,NULL,NULL,NULL,NULL),
(25,'User: logr | Created: Sample log document [Item Id: 82]','2024-08-29 14:56:36','2024-08-29 14:56:36',1,1,NULL,NULL,NULL,NULL);
/*!40000 ALTER TABLE `log` ENABLE KEYS */;
UNLOCK TABLES;
