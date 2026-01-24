from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.db import transaction

from .models import (
    PrivacyPolicy, AboutUs, TermsConditions
)
from .serializers import (
    PrivacyPolicySerializer, AboutUsSerializer, TermsConditionsSerializer,
)
from rest_framework.response import Response

from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from django.db import transaction
from rest_framework.response import Response

from .models import PrivacyPolicy, AboutUs, TermsConditions
from .serializers import PrivacyPolicySerializer, AboutUsSerializer, TermsConditionsSerializer
from account.permissions import IsSuperuserOrReadOnly


class SingleObjectViewMixin:
    def get_object(self):
        return self.queryset.first()


class BaseSingleObjectView(SingleObjectViewMixin, generics.RetrieveUpdateAPIView):
    permission_classes = [IsSuperuserOrReadOnly]

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance:
            return Response(
                {"success": False, "message": "Content not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(instance)
        return Response(
            {
                "success": True,
                "message": "Content retrieved successfully.",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    @transaction.atomic
    def put(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = (
            self.get_serializer(instance, data=request.data)
            if instance
            else self.get_serializer(data=request.data)
        )

        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "message": "Validation failed.",
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer.save()
        return Response(
            {
                "success": True,
                "message": "Content updated successfully." if instance else "Content created successfully.",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK if instance else status.HTTP_201_CREATED,
        )

    @transaction.atomic
    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = (
            self.get_serializer(instance, data=request.data, partial=True)
            if instance
            else self.get_serializer(data=request.data, partial=True)
        )

        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "message": "Validation failed.",
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer.save()
        return Response(
            {
                "success": True,
                "message": "Content partially updated successfully." if instance else "Content created successfully.",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK if instance else status.HTTP_201_CREATED,
        )



class PrivacyPolicyView(BaseSingleObjectView):
    queryset = PrivacyPolicy.objects.all()
    serializer_class = PrivacyPolicySerializer


class AboutUsView(BaseSingleObjectView):
    queryset = AboutUs.objects.all()
    serializer_class = AboutUsSerializer


class TermsConditionsView(BaseSingleObjectView):
    queryset = TermsConditions.objects.all()
    serializer_class = TermsConditionsSerializer
