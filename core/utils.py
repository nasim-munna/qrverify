import secrets
from .models import QRCode

def generate_unique_code():
    while True:
        code = secrets.token_urlsafe(24)
        if not QRCode.objects.filter(unique_code=code).exists():
            return code