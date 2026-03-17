LOCK TABLES `notification_provider` WRITE;
/*!40000 ALTER TABLE `notification_provider` DISABLE KEYS */;
INSERT INTO `notification_provider` VALUES
(1,'apprise', 'Local library for sending notifications to email, Discord, Slack, Teams, etc.', '# Apprise Notification URLs

[Apprise](https://github.com/caronc/apprise) is a local notification library — not an external service. It is used to send notifications to various platforms using the URL formats below.

## Email (SMTP)

```
mailto://user@gmail.com
```

## Microsoft Teams

```
msteams://TokenA/TokenB/TokenC
```

## Slack

```
slack://TokenA/TokenB/TokenC/#channel
```

## Custom Webhooks

```
json://hostname/path
```

For the full list of supported services, see the [Apprise Services Page](https://appriseit.com/services).');
/*!40000 ALTER TABLE `notification_provider` ENABLE KEYS */;
UNLOCK TABLES;
