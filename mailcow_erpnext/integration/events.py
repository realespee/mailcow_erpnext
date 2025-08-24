import frappe
from frappe.utils.password import get_decrypted_password

from .utils import convert_to_base64, generate_password
from .api import (
    create_mailbox, get_mailbox, create_app_password,
    delete_mailbox, find_calendars, find_contacts, 
    put_all_day_event, delete_event
)


def provision_mailbox(doc, method):
    if not doc.user_id:
        return
    
    username = doc.user_id

    if method == "on_update":
        res = get_mailbox(username)
        if not len(res.json()) == 0:
            return
        
    full_name = f"{doc.first_name} {doc.last_name}"
    reset_password = generate_password(10)
    domain = frappe.get_single_value("Mailcow Settings", "domain")
    local_part = username.split('@')[0]

    # Create Mailbox
    create_mailbox(domain=domain, local_part=local_part, full_name=full_name, password=reset_password)

    # Create and Save App Password
    if not frappe.db.exists('Mailcow DAV Password', username):
        dav_password = generate_password(12)
        create_app_password(username_email=username, app_name='ERPNext', app_password=dav_password)
        dav_doc = frappe.get_doc({'doctype':'Mailcow DAV Password', 'user_email': username, 'dav_app_password': dav_password,'reset_password': reset_password})
        dav_doc.insert()
    else:
        dav_doc = frappe.get_doc('Mailcow DAV Password', username)
        dav_password = generate_password(12)
        create_app_password(username_email=username, app_name='ERPNext', app_password=dav_doc.dav_app_password)
        dav_doc.reset_password = reset_password
        dav_doc.dav_app_password = dav_password
        dav_doc.save()
    
    msg = f'''
                <div><h5> Email for {full_name} Provisioned Successfully</h5><br><br>
                Email: {username}<br><br>
                Password: {reset_password}</div>
        '''
    frappe.msgprint(msg)

def remove_mailbox(doc, method):
    if not doc.user_id:
        return
    
    username = doc.user_id
    res = get_mailbox(username)
    if not len(res.json()) == 0:
        delete_mailbox(username)
        delete_app_password(username)


def delete_app_password(username):
    if frappe.db.exists('Mailcow DAV Password', username):
        frappe.delete_doc('Mailcow DAV Password', username)

def format_date_for_calendar(date_obj):
    from datetime import datetime
    formatted_date = date_obj.strftime("%Y%m%d")
    return formatted_date

# ==================== Calendar Changes ================================

def create_calendar_holiday(doc, method):
    user_email = frappe.db.get_value('Employee', doc.employee, 'user_id')
    base_url = frappe.db.get_single_value('Mailcow Settings', 'base_url')

    app_password = get_decrypted_password('Mailcow DAV Password', user_email, 'dav_app_password')
    summary = (doc.description or "").strip() or f"Leave {doc.name} for {doc.employee_name}"

    put_all_day_event(
        base_url=base_url,
        user_email=user_email,
        app_password=app_password,
        uid=doc.name,
        summary=summary,
        start_date=doc.from_date,
        end_date_inclusive=doc.to_date,
        calendar_name="personal",
        opaque=True,
    )


def delete_cal_event(doc, method):
    base_url = frappe.db.get_single_value('Mailcow Settings', 'base_url')
    user_email = frappe.db.get_value('Employee', doc.employee, 'user_id')
    app_password = get_decrypted_password('Mailcow DAV Password', user_email, 'dav_app_password')
    uid = doc.name

    delete_event(
        base_url=base_url,
        user_email=user_email,
        app_password=app_password,
        uid=uid
    )
