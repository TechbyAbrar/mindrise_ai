from django.urls import path
from .views import (SignupAPIView, VerifyOTPAPIView, ResendOTPView, LoginView, ForgetPasswordView, 
                    ForgetPasswordVerificationAPIView, ResetPasswordAPIView, SocialLoginAPIView, UserDeleteAPIView)

urlpatterns = [
     path("signup/", SignupAPIView.as_view(), name="signup"),
     path("verify-otp/", VerifyOTPAPIView.as_view(), name="verify-otp"),
     path("resend-otp/", ResendOTPView.as_view(), name="resend-otp"),
     path("auth/login/", LoginView.as_view(), name="login"),
     path("forget-password/", ForgetPasswordView.as_view(), name="forget-password"),
     path("verify-otp/forgetpass/", ForgetPasswordVerificationAPIView.as_view(), name="reset-password"),
     path("reset-password/", ResetPasswordAPIView.as_view(), name="reset-password"),
     path("social-login/", SocialLoginAPIView.as_view(), name="social-login"),
     path("users/<int:user_id>/delete-account/", UserDeleteAPIView.as_view(), name="delete-account"),
]
