--
-- Copyright (c) UChicago Argonne, LLC. All rights reserved.
-- See LICENSE file.
--

LOCK TABLES `property_type` WRITE;
/*!40000 ALTER TABLE `property_type` DISABLE KEYS */;
INSERT INTO `property_type` VALUES
(1,'Image',NULL,NULL,1,2,NULL,NULL,0,0,0,1,1),
(2,'Document (Upload)','',NULL,1,1,'','',0,0,0,1,1);
/*!40000 ALTER TABLE `property_type` ENABLE KEYS */;
UNLOCK TABLES;
