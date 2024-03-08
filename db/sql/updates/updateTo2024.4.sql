DROP TABLE IF EXISTS `user_session`;
CREATE TABLE `user_session` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `user_id` int(11) unsigned NOT NULL,
  `session_name` varchar(128) DEFAULT NULL,
  `expiration_date_time` datetime NOT NULL,
  `session_key` varchar(256) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `user_session_k1` (`user_id`),
  CONSTRAINT `user_session_fk1` FOREIGN KEY (`user_id`) REFERENCES `user_info` (`id`) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;