"""
File: services.py
Author: Hamdy El-Madbouly
Description: Asynchronous service layer for User management.
Handles background tasks such as sending verification emails, password reset links,
and security alerts to prevent blocking the main API thread.
"""

from .tasks import (
    send_verification_email_task,
    send_forgot_password_email_task,
    send_security_alert_task,
)


def send_verification_email(user, token):
    send_verification_email_task.delay(user.id, token)


def send_forgot_password_email(user, token):
    send_forgot_password_email_task.delay(user.id, token)


def too_many_requests_email(user_email, msg):
    send_security_alert_task.delay(user_email, msg)
