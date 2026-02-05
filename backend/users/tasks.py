from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model

from celery import shared_task


@shared_task
def send_verification_email_task(user_id, token_string):
    User = get_user_model()
    try:
        user = User.objects.get(id=user_id)
        verification_link = f"http://localhost:3000/verify-email/?token={token_string}"
        send_mail(
            subject="Verify your email",
            message=f"Click this link to verify your account: {verification_link}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
        )
    except User.DoesNotExist:
        pass


@shared_task
def send_forgot_password_email_task(user_id, token_string):
    User = get_user_model()
    try:
        user = User.objects.get(id=user_id)
        verification_link = (
            f"http://localhost:3000/reset-password/?token={token_string}"
        )
        send_mail(
            subject="Password Reset",
            message=f"Click this link to reset your password: {verification_link}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
        )
    except User.DoesNotExist:
        pass


@shared_task
def send_security_alert_task(user_email, msg):
    send_mail(
        subject="Security Alert",
        message=f"Hello, we noticed a strange activity coming from your account: {msg}. If this was you, please keep in mind this may be considered a security alert on our side and might lead to account deactivation if persistent. Otherwise, ignore this email.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user_email],
    )


@shared_task
def send_otp_sms_task(phone_number, otp):
    """Send OTP via SMS asynchronously"""
    from .sms_service import send_otp_sms

    send_otp_sms(phone_number, otp)
