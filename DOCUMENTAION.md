# Mailcow ERPNext Integration Documentation

## Overview

Mailcow ERPNext is a Frappe/ERPNext custom app that integrates Mailcow email server management directly into ERPNext. It enables automatic provisioning and management of Mailcow mailboxes and DAV app passwords for employees, as well as calendar event synchronization for leave applications.

---

## Features

- **Automatic Mailbox Provisioning:** When an Employee is created or updated, a Mailcow mailbox is provisioned.
- **DAV App Password Management:** Secure DAV app passwords are generated and stored for each user.
- **Calendar Integration:** Leave applications automatically create and remove calendar events in Mailcow/SOGo.
- **Mailbox Removal:** Deleting an Employee removes their Mailcow mailbox and DAV credentials.

---

## Setup

1. **Install the App**

   Use the bench CLI to get and install the app:

   ```bash
   cd $PATH_TO_YOUR_BENCH
   bench get-app $URL_OF_THIS_REPO --branch develop
   bench install-app mailcow_erpnext
   ```

2. **Configure Mailcow Settings**

   - Go to **Mailcow Settings** in ERPNext.
   - Fill in:
     - **Base URL:** Your Mailcow server URL (e.g., `https://mail.example.com`)
     - **API Key:** Your Mailcow API key
     - **Domain:** The email domain to provision (e.g., `example.com`)
     - **Default Quota:** (Optional) Default mailbox quota in MB

---

## Usage

### Employee Mailbox Provisioning

- When you create or update an Employee with a valid `user_id` (email), the app will:
  - Provision a Mailcow mailbox for the user.
  - Generate and save a DAV app password in the **Mailcow DAV Password** doctype.
  - Display the mailbox credentials.

### Removing Mailboxes

- When you delete an Employee, their Mailcow mailbox and DAV app password record are removed automatically.

### Calendar Sync for Leave Applications

- When a Leave Application is submitted:
  - An all-day event is created in the user's Mailcow/SOGo calendar.
- When a Leave Application is cancelled:
  - The corresponding calendar event is deleted.

---

## Developer Notes

- All integration logic is handled in [`mailcow_erpnext/integration/events.py`](mailcow_erpnext/mailcow_erpnext/integration/events.py).
- API interactions with Mailcow are in [`mailcow_erpnext/integration/api.py`](mailcow_erpnext/mailcow_erpnext/integration/api.py).
- Utility functions are in [`mailcow_erpnext/integration/utils.py`](mailcow_erpnext/mailcow_erpnext/integration/utils.py).

---

## Troubleshooting

- Ensure Mailcow API credentials and base URL are correct in **Mailcow Settings**.
- Check ERPNext logs for integration errors.
- Make sure the Employee `user_id` matches the intended email address.

---

## License

MIT License
