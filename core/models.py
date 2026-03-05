
import uuid
from django.db import models
from django.core.files.base import ContentFile
import qrcode
from io import BytesIO


class Product(models.Model):
    name = models.CharField(max_length=255)
    sku_code = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    total_qr_generated = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
class QRCode(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    unique_code = models.CharField(max_length=64, unique=True, db_index=True)
    qr_image = models.ImageField(upload_to="qrcodes/", blank=True, null=True)

    is_scanned = models.BooleanField(default=False)
    first_scanned_at = models.DateTimeField(null=True, blank=True)
    scan_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.qr_image:
            self.generate_qr_image()
        super().save(*args, **kwargs)

    def generate_qr_image(self):
        qr_data = f"http://127.0.0.1:8000/verify/{self.unique_code}/"

        qr = qrcode.QRCode(
            version=None,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        buffer = BytesIO()
        img.save(buffer, format="PNG")

        file_name = f"{self.unique_code}.png"
        self.qr_image.save(file_name, ContentFile(buffer.getvalue()), save=False)
    
class ScanLog(models.Model):
    qr_code = models.ForeignKey(QRCode, on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    user_agent = models.TextField(blank=True)
    scanned_at = models.DateTimeField(auto_now_add=True)