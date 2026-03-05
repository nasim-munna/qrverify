import os
from django.shortcuts import render
from django.utils import timezone
from django.conf import settings
from ipware import get_client_ip
from geoip2.database import Reader
from django.db.models import F
from .models import QRCode, ScanLog

from django.db.models import Count, Sum
from django.contrib.admin.views.decorators import staff_member_required
from .models import Product, QRCode, ScanLog


MAX_SCAN_LIMIT = 5


def get_country_from_ip(ip):
    """
    Returns country name from IP using GeoLite2 database.
    """
    if not ip:
        return "Unknown"

    try:
        db_path = os.path.join(settings.GEOIP_PATH, "GeoLite2-Country.mmdb")
        reader = Reader(db_path)
        response = reader.country(ip)
        return response.country.name or "Unknown"
    except:
        return "Unknown"


def verify_qr(request, unique_code):
    """
    Public QR verification view.
    Handles:
    - Invalid code
    - Scan limit
    - First scan detection
    - Country detection
    - Logging
    """

    qr = QRCode.objects.select_related("product").filter(
        unique_code=unique_code
    ).first()

    # Invalid QR
    if not qr:
        return render(request, "verify_invalid.html")

    # Get real client IP
    ip, is_routable = get_client_ip(request)

    # In local development, IP becomes 127.0.0.1
    # So we fallback to None
    if ip == "127.0.0.1":
        ip = None

    country = get_country_from_ip(ip)

    is_first_scan = False
    is_blocked = False

    # Scan limit check
    if qr.scan_count >= MAX_SCAN_LIMIT:
        is_blocked = True
    else:
        if qr.scan_count == 0:
            qr.is_scanned = True
            qr.first_scanned_at = timezone.now()
            is_first_scan = True

        QRCode.objects.filter(id=qr.id).update(scan_count=F("scan_count") + 1)
        

        # Log scan
        ScanLog.objects.create(
            qr_code=qr,
            ip_address=ip,
            country=country,
            user_agent=request.META.get("HTTP_USER_AGENT", "")
        )

    context = {
        "product": qr.product,
        "is_first_scan": is_first_scan,
        "is_blocked": is_blocked,
        "scan_count": qr.scan_count,
        "country": country,
        "max_limit": MAX_SCAN_LIMIT,
    }

    return render(request, "verify_result.html", context)


@staff_member_required
def dashboard_view(request):
    total_products = Product.objects.count()
    total_qr = QRCode.objects.count()
    total_scans = ScanLog.objects.count()

    # Duplicate scans = total scans - first scans
    first_scans = QRCode.objects.filter(is_scanned=True).count()
    duplicate_scans = total_scans - first_scans

    # Country aggregation
    country_stats = (
        ScanLog.objects
        .values("country")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    context = {
        "total_products": total_products,
        "total_qr": total_qr,
        "total_scans": total_scans,
        "duplicate_scans": duplicate_scans,
        "country_stats": country_stats,
    }

    return render(request, "dashboard.html", context)