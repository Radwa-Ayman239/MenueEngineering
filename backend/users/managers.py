import secrets
from django.core.cache import cache
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired

from django.contrib.auth.base_user import BaseUserManager


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")

        first_name = extra_fields.get("first_name", "")
        last_name = extra_fields.get("last_name", "")

        if not first_name:
            raise ValueError("The First Name field must be set")
        if not last_name:
            raise ValueError("The Last Name field must be set")

        phone_number = extra_fields.get("phone_number")
        if not phone_number:
            raise ValueError("The Phone Number field must be set for 2FA")

        extra_fields.setdefault("is_active", False)
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("type", "admin")

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True")

        return self.create_user(email, password, **extra_fields)


class TokenManager:
    @staticmethod
    def _generate_signed_token():
        raw_token = secrets.token_urlsafe(32)
        signer = TimestampSigner()
        return signer.sign(raw_token)

    @staticmethod
    def _validate_signed_token(token, max_age):
        signer = TimestampSigner()
        try:
            signer.unsign(token, max_age=max_age)
            return True
        except (BadSignature, SignatureExpired):
            return False

    @classmethod
    def set_email_verification_token(cls, user_id):
        token = cls._generate_signed_token()
        key = f"email_verify:{token}"
        cache.set(key, user_id, timeout=86400)
        return token

    @classmethod
    def validate_email_verification_token(cls, token):
        if not cls._validate_signed_token(token, max_age=86400):
            return None

        key = f"email_verify:{token}"
        user_id = cache.get(key)
        if user_id:
            cache.delete(key)
            return user_id
        return None

    @classmethod
    def set_password_reset_token(cls, user_id):
        token = cls._generate_signed_token()
        key = f"password_reset:{token}"
        cache.set(key, user_id, timeout=900)
        return token

    @classmethod
    def validate_password_reset_token(cls, token):
        if not cls._validate_signed_token(token, max_age=900):
            return None

        key = f"password_reset:{token}"
        user_id = cache.get(key)
        if user_id:
            cache.delete(key)
            return user_id
        return None

    @classmethod
    def _generate_complex_otp(cls, length=8):
        """Generate complex alphanumeric OTP excluding confusing characters (O, 0, I, 1, l)"""
        # Use uppercase letters + digits, excluding O/0/I/1/l for clarity
        alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        return "".join(secrets.choice(alphabet) for _ in range(length))

    @classmethod
    def set_otp_token(cls, user_id, phone_number):
        """Generate complex OTP, store in Redis with 5-minute expiry"""
        otp = cls._generate_complex_otp()
        key = f"otp:{phone_number}"
        cache.set(key, {"otp": otp, "user_id": str(user_id)}, timeout=300)
        return otp

    @classmethod
    def validate_otp(cls, phone_number, otp):
        """Validate OTP and return user_id if valid"""
        key = f"otp:{phone_number}"
        data = cache.get(key)
        if data and data["otp"].upper() == otp.upper():
            cache.delete(key)
            return data["user_id"]
        return None
