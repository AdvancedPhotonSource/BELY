LOCK TABLES `entity_type` WRITE;
/*!40000 ALTER TABLE `entity_type` DISABLE KEYS */;
INSERT INTO `entity_type` VALUES
(1,'Template', 'classification for template items'),
(2,'aop','.'),
(3,'ctl','.'),
(4,'ops','.');
/*!40000 ALTER TABLE `entity_type` ENABLE KEYS */;
UNLOCK TABLES;
