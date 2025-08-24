import requests
import frappe
import random
import string
import json
import requests, uuid
from datetime import datetime, timedelta
from frappe.utils.password import get_decrypted_password
from frappe.exceptions import LinkExistsError
from .utils import _date_ics


   
def _headers():
    api_key = frappe.db.get_single_value("Mailcow Settings", "api_key")
    return {"X-API-Key": api_key, "Content-Type": "application/json"}

def create_mailbox(domain, local_part, full_name, password, quota_mb=1024):
    base = frappe.db.get_single_value("Mailcow Settings", "base_url").rstrip("/")
    domain = frappe.get_single_value("Mailcow Settings", "domain")

    default_quota = frappe.db.get_single_value("Mailcow Settings", "default_quota")
    quota_mb = default_quota if default_quota else quota_mb

    payload = {
        "active": True,
        "domain": domain,
        "local_part": local_part,
        "name": full_name,
        "password": password,
        "password2": password,
        "quota": quota_mb,
        "force_pw_update": True,
        "tls_enforce_in": True,
        "tls_enforce_out": True,
    }
    url = f"{base}/api/v1/add/mailbox"
    r = requests.post(url, json=payload, headers=_headers(), timeout=15)
    r.raise_for_status()
    return r.json()

def get_mailbox(username_email):
    base = frappe.db.get_single_value("Mailcow Settings", "base_url").rstrip("/")
    url = f"{base}/api/v1/get/mailbox/{username_email}"

    response = requests.request('GET', url, headers=_headers(), data = {})
    return response

def create_app_password(username_email, app_name, app_password, protocols=("dav_access",)):
    base = frappe.db.get_single_value("Mailcow Settings", "base_url").rstrip("/")
    payload = {
        "active": True,
        "username": username_email,
        "app_name": app_name,
        "app_passwd": app_password,
        "app_passwd2": app_password,
        "protocols": list(protocols)
    }
    url = f"{base}/api/v1/add/app-passwd"
    r = requests.post(url, json=payload, headers=_headers(), timeout=15)
    r.raise_for_status()
    return r.json()

def delete_mailbox(username_email):
    base = frappe.db.get_single_value("Mailcow Settings", "base_url").rstrip("/")
    payload = payload = json.dumps([username_email])

    url = f"{base}/api/v1/delete/mailbox"
    try:
        response = requests.request('POST', url, headers=_headers(), data=payload)
        response.raise_for_status()
        return response.json()
    except LinkExistsError as e: # user or user permissions may still be linked to this employee
        frappe.throw(str(e))
    except requests.exceptions.RequestException as e:
        frappe.throw(f"Failed to delete mailbox: {str(e)}")

def find_calendars(username_email, app_password):
    base = frappe.db.single_value("Mailcow Settings", "base_url").rstrip("/")
    payload = ''
    headers = {
        'Depth': '1',
        'Content-Type': 'application/xml',
        'Authorization': f'Basic {app_password}',
    }
    url = f'{base}/SOGo/dav/{username_email}/Calendar/personal/'
    response = requests.request("PROPFIND", url, headers=headers, data=payload)
    return response.text

def find_contacts(username_email, app_password):
    base = frappe.db.single_value("Mailcow Settings", "base_url").rstrip("/")
    payload = ''
    headers = {
        'Depth': '1',
        'Content-Type': 'application/xml',
        'Authorization': f'Basic {app_password}',
    }
    url = f'{base}/SOGo/dav/{username_email}/Contacts/personal/'
    response = requests.request("PROPFIND", url, headers=headers, data=payload)
    return response.text

def put_all_day_event(
    base_url: str,
    user_email: str,
    app_password: str,
    uid: str,
    summary: str,
    start_date, 
    end_date_inclusive, 
    calendar_name: str = "personal",
    opaque: bool = True,
):
    start_ics = _date_ics(start_date)
    # CalDAV all-day DTEND must be exclusive -> add 1 day
    if isinstance(end_date_inclusive, str):
        end_d = frappe.utils.getdate(end_date_inclusive)
    else:
        end_d = end_date_inclusive
    end_exclusive_ics = (end_d + timedelta(days=1)).strftime("%Y%m%d")

    uid = uid or f"{uuid.uuid4()}@erpnext"
    ics = (
        "BEGIN:VCALENDAR\r\n"
        "VERSION:2.0\r\n"
        "PRODID:-//ERPNext//Leave//EN\r\n"
        "BEGIN:VEVENT\r\n"
        f"UID:{uid}\r\n"
        f"DTSTAMP:{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}\r\n"
        f"SUMMARY:{summary or 'Leave'}\r\n"
        f"DTSTART;VALUE=DATE:{start_ics}\r\n"
        f"DTEND;VALUE=DATE:{end_exclusive_ics}\r\n"
        f"TRANSP:{'OPAQUE' if opaque else 'TRANSPARENT'}\r\n"
        "STATUS:CONFIRMED\r\n"
        "END:VEVENT\r\n"
        "END:VCALENDAR\r\n"
    )

    url = f"{base_url.rstrip('/')}/SOGo/dav/{user_email}/Calendar/{calendar_name}/{uid}.ics"
    try:
        r = requests.put(
            url,
            data=ics.encode("utf-8"),
            headers={"Content-Type": "text/calendar", "If-None-Match": "*"},
            auth=(user_email, app_password),
            timeout=20,
        )
        r.raise_for_status()
        return {"ok": True, "status": r.status_code, "etag": r.headers.get("ETag"), "url": url, "uid": uid}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "CalDAV PUT failed")
        frappe.throw("Failed to push calendar entry to SOGo. See Error Log for details.\n", e)

def delete_event(
    base_url: str,
    user_email: str,
    app_password: str,
    uid: str,
    calendar_name: str = "personal",
):
    url = f"{base_url.rstrip('/')}/SOGo/dav/{user_email}/Calendar/{calendar_name}/{uid}.ics"
    r = requests.delete(url, auth=(user_email, app_password), timeout=15)
    if r.status_code not in (200, 204):
        frappe.log_error(f"Delete failed {r.status_code} {r.text}", "CalDAV DELETE")
        frappe.throw("Failed to remove calendar entry in SOGo.")
    return {"ok": True}

