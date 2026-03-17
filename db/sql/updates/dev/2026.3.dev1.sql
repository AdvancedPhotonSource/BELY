--
-- Copyright (c) UChicago Argonne, LLC. All rights reserved.
-- See LICENSE file.
--

ALTER TABLE `notification_provider` ADD COLUMN `instructions` TEXT DEFAULT NULL;

UPDATE `notification_provider` SET
  `description` = 'Sends notifications to email, Discord, Slack, Teams, and more.',
  `instructions` = '# Notification URL Examples

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

**Note:** Notifications are powered by [Apprise](https://github.com/caronc/apprise), an open-source notification library hosted locally.'
WHERE `name` = 'apprise';
