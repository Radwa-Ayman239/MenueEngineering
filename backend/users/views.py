"""
API Views for 2FA authentication system.
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from knox.auth import TokenAuthentication
from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes

from .serializers import (
    CreateUserSerializer,
    ActivateAccountSerializer,
    LoginStep1Serializer,
    LoginStep2Serializer,
    ResendActivationSerializer,
    RefreshTokenSerializer,
    ForgotPasswordRequestSerializer,
    ForgotPasswordResetSerializer,
)
from .permissions import IsAdminOrManager, CanCreateUserType


class CreateUserView(APIView):
    """
    Create a new user (Manager or Staff).
    - Admin can create: Manager, Staff
    - Manager can create: Staff only
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsAdminOrManager, CanCreateUserType]

    @extend_schema(
        summary="Create New User",
        description="Admin creates Managers/Staff, Managers create Staff only. Sends activation email.",
        tags=['User Management'],
        request=CreateUserSerializer,
        responses={
            201: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
        },
        auth=[{'TokenAuthentication': []}]
    )
    def post(self, request):
        serializer = CreateUserSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "message": "User created successfully. Activation email sent.",
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "type": user.type,
                },
            },
            status=status.HTTP_201_CREATED,
        )


class ActivateAccountView(APIView):
    """
    Activate account by setting password via email token.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Activate Account",
        description="Set password and activate account using email verification token.",
        tags=['Authentication'],
        request=ActivateAccountSerializer,
        responses={
            200: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
        }
    )
    def post(self, request):
        serializer = ActivateAccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return Response(result, status=status.HTTP_200_OK)


class ResendActivationView(APIView):
    """
    Resend activation email for unactivated accounts.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Resend Activation Email",
        description="Send activation email to unverified user.",
        tags=['Authentication'],
        request=ResendActivationSerializer,
        responses={
            200: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
        }
    )
    def post(self, request):
        serializer = ResendActivationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return Response(result, status=status.HTTP_200_OK)


class LoginStep1View(APIView):
    """
    Login Step 1: Validate password and send OTP.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Login Step 1 - Send OTP",
        description="Validate email/password, send OTP via SMS. Returns session token for step 2.",
        tags=['Authentication'],
        request=LoginStep1Serializer,
        responses={
            200: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
        }
    )
    def post(self, request):
        serializer = LoginStep1Serializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        result = serializer.create_session_and_send_otp()
        return Response(result, status=status.HTTP_200_OK)


class LoginStep2View(APIView):
    """
    Login Step 2: Verify OTP and return access token.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Login Step 2 - Verify OTP",
        description="Verify OTP from SMS, returns access/refresh tokens.",
        tags=['Authentication'],
        request=LoginStep2Serializer,
        responses={
            200: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
        }
    )
    def post(self, request):
        serializer = LoginStep2Serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.create_tokens()
        return Response(result, status=status.HTTP_200_OK)


class RefreshTokenView(APIView):
    """
    Refresh access token using refresh token.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Refresh Access Token",
        description="Use refresh token to obtain new access token.",
        tags=['Authentication'],
        request=RefreshTokenSerializer,
        responses={
            200: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
        }
    )
    def post(self, request):
        serializer = RefreshTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return Response(result, status=status.HTTP_200_OK)


class ForgotPasswordRequestView(APIView):
    """
    Request password reset link via email.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Request Password Reset",
        description="Send password reset link to email. Returns generic success message for security.",
        tags=['Authentication'],
        request=ForgotPasswordRequestSerializer,
        responses={
            200: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
        }
    )
    def post(self, request):
        serializer = ForgotPasswordRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {
                "detail": "If an account exists with this email, a password reset link has been sent."
            },
            status=status.HTTP_200_OK,
        )


class ForgotPasswordResetView(APIView):
    """
    Reset password using token from email.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Reset Password",
        description="Reset user password using token from email. Requires matching passwords.",
        tags=['Authentication'],
        request=ForgotPasswordResetSerializer,
        responses={
            200: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
        }
    )
    def post(self, request):
        serializer = ForgotPasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return Response(result, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """
    Logout user by deleting their tokens.
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Logout",
        description="Logout user and invalidate their tokens.",
        tags=['Authentication'],
        request=None,
        responses={
            200: OpenApiTypes.OBJECT,
            401: OpenApiTypes.OBJECT,
        },
        auth=[{'TokenAuthentication': []}]
    )
    def post(self, request):
        # Delete all tokens for this user
        request._auth.delete()
        return Response(
            {"detail": "Successfully logged out."}, status=status.HTTP_200_OK
        )
