from django.contrib import admin
from django.http import HttpResponse
from django.shortcuts import render, redirect
import csv

from .models import Product, QRCode, ScanLog
from .utils import generate_unique_code


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku_code', 'total_qr_generated')

    change_form_template = "admin/product_change_form.html"

    def response_change(self, request, obj):
        if "_generate_qr" in request.POST:
            quantity = int(request.POST.get("quantity"))
            codes = []

            for _ in range(quantity):
                code = generate_unique_code()
                
                qr = QRCode(
                    product=obj,
                    unique_code=code
                )
                qr.save()
                codes.append(code)

            obj.total_qr_generated += quantity
            obj.save()

            # Export CSV
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="qr_codes.csv"'

            writer = csv.writer(response)
            writer.writerow(["Unique Code", "Verification URL"])

            for code in codes:
                url = f"https://yourdomain.com/verify/{code}"
                writer.writerow([code, url])

            return response

        return super().response_change(request, obj)


admin.site.register(QRCode)
admin.site.register(ScanLog)