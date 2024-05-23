LOCK TABLES `entity_type` WRITE;
/*!40000 ALTER TABLE `entity_type` DISABLE KEYS */;
INSERT INTO `entity_type` VALUES
(1,'Template','Template',NULL,'classification for template items',NULL,NULL,NULL,NULL,1),
(2,'studies','Machine Studies',NULL,'.',NULL,NULL,NULL,1.00,0),
(3,'maintenance','Maintenance',NULL,'.',NULL,NULL,NULL,2.00,0),
(4,'ops','Operations','','.','opsList',NULL,NULL,3.00,0),
(5,'sandbox','Sandbox','','entity type for playing around and testing features of logr.',NULL,NULL,NULL,999.00,0),
(6,'ctl','Controls',NULL,'',NULL,3,NULL,NULL,0),
(7,'studies-sr','SR','SR Studies','','studiesList',2,NULL,NULL,0),
(8,'injector','Injector','Injector Studies','','studiesList',2,NULL,NULL,0),
(9,'vacuum','Vacuum','','',NULL,3,NULL,NULL,0),
(10,'power','Power Systems','','',NULL,3,NULL,NULL,0),
(11,'diag','Diagnostics','','',NULL,3,NULL,NULL,0),
(12,'aop-apps','Physics Applications','','',NULL,3,NULL,NULL,0),
(13,'id','Insertion Devices','','',NULL,3,NULL,NULL,0),
(14,'rf','RF','','',NULL,3,NULL,NULL,0);
/*!40000 ALTER TABLE `entity_type` ENABLE KEYS */;
UNLOCK TABLES;
