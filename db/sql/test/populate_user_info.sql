LOCK TABLES `user_info` WRITE;
SET SESSION FOREIGN_KEY_CHECKS=0;
/*!40000 ALTER TABLE `user_info` DISABLE KEYS */;
INSERT INTO `user_info` VALUES
(1,'logr','LOGR','System Account','','logr@aps.anl.gov','aNX5$whZeG05Yq7xgrO8lah3oZilG5mAQAVaJ',''),
(2,'user','User','Standard','','','nQs4$9GXkrvqFf8+eFmRfK3uskEfun51bycyx','');
/*!40000 ALTER TABLE `user_info` ENABLE KEYS */;
UNLOCK TABLES;
