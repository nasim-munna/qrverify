from .views import verify_qr, dashboard_view
from django.urls import path,include

urlpatterns = [
    path("verify/<str:unique_code>/", verify_qr, name="verify_qr"),
    path("dashboard/", dashboard_view, name="dashboard"),
]