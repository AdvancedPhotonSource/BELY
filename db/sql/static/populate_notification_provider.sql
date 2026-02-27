LOCK TABLES `notification_provider` WRITE;
/*!40000 ALTER TABLE `notification_provider` DISABLE KEYS */;
INSERT INTO `notification_provider` VALUES
(1,'apprise', 'Apprise unified notification library supporting email, Discord, Slack, Teams, etc.', '# Apprise Notification URLs

[Apprise](https://github.com/caronc/apprise) supports many notification services. Below are some common URL formats.

## Email (SMTP)

```
mailto://user:password@gmail.com
```

## Slack

```
slack://TokenA/TokenB/TokenC/#channel
```

## Discord

```
discord://WebhookID/WebhookToken
```

## Microsoft Teams

```
msteams://TokenA/TokenB/TokenC
```

## Custom Webhooks

```
json://hostname/path
```

For the full list of supported services, see the [Apprise Wiki](https://github.com/caronc/apprise/wiki).');
/*!40000 ALTER TABLE `notification_provider` ENABLE KEYS */;
UNLOCK TABLES;
