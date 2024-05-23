--
-- Copyright (c) UChicago Argonne, LLC. All rights reserved.
-- See LICENSE file.
--

LOCK TABLES `reaction` WRITE;
/*!40000 ALTER TABLE `reaction` DISABLE KEYS */;
INSERT INTO `reaction` VALUES
(1,'Like',128077,NULL,1.0),
(2,'Thinking',129300,NULL,2.0),
(3,'Great Job!',128175,NULL,3.0),
(4,'Laugh',128516,NULL,4.0),
(5,"Celebrate",127881,NULL,5.0);
/*!40000 ALTER TABLE `reaction` ENABLE KEYS */;
UNLOCK TABLES;
