from django.urls import path
from .views import UserInformationList

urlpatterns = [
    path('users/list/', UserInformationList.as_view(), name='user-subscription-list'),
]
