--
-- Copyright (c) UChicago Argonne, LLC. All rights reserved.
-- See LICENSE file.
--

ALTER TABLE `notification_provider` ADD COLUMN `instructions` TEXT DEFAULT NULL;

UPDATE `notification_provider` SET `instructions` = '# Apprise Notification URLs

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

For the full list of supported services, see the [Apprise Services Page](https://appriseit.com/services).'
WHERE `name` = 'apprise';
