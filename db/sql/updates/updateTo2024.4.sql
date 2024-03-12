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


delimiter //

DROP PROCEDURE IF EXISTS cleanup_sessions;//
CREATE PROCEDURE `cleanup_sessions` () 
BEGIN
	DELETE FROM user_session WHERE expiration_date_time < CURRENT_TIMESTAMP();
END //

-- Ensure that event_scheduler is on
-- https://mariadb.com/docs/server/ref/mdb/system-variables/event_scheduler/
DROP EVENT IF EXISTS session_clean_event;//
CREATE EVENT session_clean_event 
ON SCHEDULE EVERY 1 HOUR STARTS CURRENT_TIMESTAMP
DO
  CALL cleanup_sessions(); // 

-- Run as db admin to start during runtime. 
-- SET GLOBAL event_scheduler=ON;