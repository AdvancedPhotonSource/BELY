---
globs: examples/handlers/apprise_smart_notification/**/*.py
description: Guidelines for maintaining email threading functionality in the
  Apprise Smart Notification Handler
alwaysApply: false
---

When modifying the Apprise Smart Notification Handler:
1. Email notifications must use threading headers (In-Reply-To, References, Thread-Topic) to group related messages
2. Subject lines for email notifications should follow the pattern "Re: Log: [Document Name]" with optional suffixes like "[Entry Updated]" or "[by username]"
3. Non-email notifications should use descriptive subjects with emojis
4. The EmailThreadingStrategy class should detect email URLs and only apply threading to email notifications
5. Test assertions must account for different subject formats between email and non-email notifications
6. Mock notification tracking functions in tests must accept an optional headers parameter for email threading support