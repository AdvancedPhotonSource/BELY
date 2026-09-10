--
-- Copyright (c) UChicago Argonne, LLC. All rights reserved.
-- See LICENSE file.
--

LOCK TABLES `notification_provider` WRITE;
/*!40000 ALTER TABLE `notification_provider` DISABLE KEYS */;
INSERT INTO `notification_provider` VALUES
(1,'apprise','Sends notifications to email, Discord, Slack, Teams, and more.','# Notification URL Examples\n\n## Email (SMTP)\n\n```\nmailto://user@gmail.com\n```\n\n## Microsoft Teams\n\n```\nmsteams://TokenA/TokenB/TokenC\n```\n\n## Slack\n\n```\nslack://TokenA/TokenB/TokenC/#channel\n```\n\n## Custom Webhooks\n\n```\njson://hostname/path\n```\n\nFor the full list of supported services, see the [Apprise Services Page](https://appriseit.com/services).\n\n---\n\n**Note:** Notifications are powered by [Apprise](https://github.com/caronc/apprise), an open-source notification library hosted locally.');
/*!40000 ALTER TABLE `notification_provider` ENABLE KEYS */;
UNLOCK TABLES;
