from django.urls import path
from .views import SignupAPIView, VerifyOTPAPIView, ResendOTPView

urlpatterns = [
     path("signup/", SignupAPIView.as_view(), name="signup"),
     path("verify-otp/", VerifyOTPAPIView.as_view(), name="verify-otp"),
     path("resend-otp/", ResendOTPView.as_view(), name="resend-otp"),
]
