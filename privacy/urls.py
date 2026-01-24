# app_name/urls.py
from django.urls import path
from .views import (
    PrivacyPolicyView,
    AboutUsView,
    TermsConditionsView,
)

urlpatterns = [
    path("privacy-policy/", PrivacyPolicyView.as_view(), name="privacy-policy"),
    path("about-us/", AboutUsView.as_view(), name="about-us"),
    path("terms-conditions/", TermsConditionsView.as_view(), name="terms-conditions"),
]
