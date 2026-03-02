--
-- Copyright (c) UChicago Argonne, LLC. All rights reserved.
-- See LICENSE file.
--

ALTER TABLE `notification_provider` ADD COLUMN `instructions` TEXT DEFAULT NULL;

UPDATE `notification_provider` SET `instructions` = '# Apprise Notification URLs

[Apprise](https://github.com/caronc/apprise) supports many notification services. Below are some common URL formats.

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

For the full list of supported services, see the [Apprise Serivces Page](https://appriseit.com/services).'
WHERE `name` = 'apprise';
