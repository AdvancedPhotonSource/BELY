LOCK TABLES `notification_provider` WRITE;
/*!40000 ALTER TABLE `notification_provider` DISABLE KEYS */;
INSERT INTO `notification_provider` VALUES
(1,'apprise', 'Sends notifications to email, Discord, Slack, Teams, and more.', '# Notification URL Examples

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

For the full list of supported services, see the [Apprise Services Page](https://appriseit.com/services).

---

**Note:** Notifications are powered by [Apprise](https://github.com/caronc/apprise), an open-source notification library hosted locally.');
/*!40000 ALTER TABLE `notification_provider` ENABLE KEYS */;
UNLOCK TABLES;
