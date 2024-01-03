LOCK TABLES `user_info` WRITE;
SET SESSION FOREIGN_KEY_CHECKS=0;
/*!40000 ALTER TABLE `user_info` DISABLE KEYS */;
INSERT INTO `user_info` VALUES
(1,'logr','LOGR','System Account',NULL,'logr@aps.anl.gov','eNDZ$AFgzHnuqfn0XB+z15LnTYEVwXAquXInL',NULL);
/*!40000 ALTER TABLE `user_info` ENABLE KEYS */;
UNLOCK TABLES;
