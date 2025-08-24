
import frappe
import random
import string
import base64
from urllib.parse import urljoin




def generate_password(length: int = 16) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#%^*()-_=+"
    return "".join(random.SystemRandom().choice(alphabet) for _ in range(length))

def _generate_password(length):
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(characters) for i in range(length))
    return password

def _date_ics(d):  # d can be date or string "YYYY-MM-DD"
    if isinstance(d, str):
        d = frappe.utils.getdate(d)
    return d.strftime("%Y%m%d")

def convert_to_base64(auth_str):
    bytes_data = auth_str.encode('utf-8')
    encoded_bytes = base64.b64encode(bytes_data)
    base64_string = encoded_bytes.decode('utf-8')
    return f'Basic {base64_string}'

