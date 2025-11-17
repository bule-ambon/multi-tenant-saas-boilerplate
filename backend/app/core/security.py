"""
Security utilities for authentication, encryption, and password management
"""
import secrets
from datetime import datetime, timedelta
from typing import Any, Optional, Union

import pyotp
import qrcode
import qrcode.image.svg
from cryptography.fernet import Fernet
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration
ALGORITHM = "HS256"


class PasswordValidator:
    """Validate passwords against security policies"""

    @staticmethod
    def validate(password: str) -> tuple[bool, Optional[str]]:
        """
        Validate password against security policy
        Returns: (is_valid, error_message)
        """
        if len(password) < settings.PASSWORD_MIN_LENGTH:
            return False, f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters"

        if settings.PASSWORD_REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter"

        if settings.PASSWORD_REQUIRE_LOWERCASE and not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter"

        if settings.PASSWORD_REQUIRE_DIGIT and not any(c.isdigit() for c in password):
            return False, "Password must contain at least one digit"

        if settings.PASSWORD_REQUIRE_SPECIAL:
            special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
            if not any(c in special_chars for c in password):
                return False, "Password must contain at least one special character"

        return True, None


class PasswordManager:
    """Password hashing and verification"""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt"""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def needs_rehash(hashed_password: str) -> bool:
        """Check if password hash needs updating"""
        return pwd_context.needs_update(hashed_password)


class TokenManager:
    """JWT token creation and verification"""

    @staticmethod
    def create_access_token(
        subject: Union[str, Any],
        expires_delta: Optional[timedelta] = None,
        additional_claims: Optional[dict] = None,
    ) -> str:
        """Create JWT access token"""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )

        to_encode = {
            "exp": expire,
            "sub": str(subject),
            "type": "access",
            "iat": datetime.utcnow(),
        }

        if additional_claims:
            to_encode.update(additional_claims)

        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=ALGORITHM
        )
        return encoded_jwt

    @staticmethod
    def create_refresh_token(
        subject: Union[str, Any],
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """Create JWT refresh token"""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                days=settings.REFRESH_TOKEN_EXPIRE_DAYS
            )

        to_encode = {
            "exp": expire,
            "sub": str(subject),
            "type": "refresh",
            "iat": datetime.utcnow(),
        }

        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=ALGORITHM
        )
        return encoded_jwt

    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Optional[str]:
        """
        Verify JWT token and return subject
        Returns None if token is invalid
        """
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[ALGORITHM]
            )

            # Verify token type
            if payload.get("type") != token_type:
                return None

            subject: str = payload.get("sub")
            if subject is None:
                return None

            return subject

        except JWTError:
            return None

    @staticmethod
    def decode_token(token: str) -> Optional[dict]:
        """Decode token without verification (for inspection)"""
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[ALGORITHM],
                options={"verify_signature": False},
            )
            return payload
        except JWTError:
            return None

    @staticmethod
    def create_password_reset_token(email: str) -> str:
        """Create password reset token"""
        expire = datetime.utcnow() + timedelta(hours=1)
        to_encode = {
            "exp": expire,
            "sub": email,
            "type": "password_reset",
            "iat": datetime.utcnow(),
        }
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def create_email_verification_token(email: str) -> str:
        """Create email verification token"""
        expire = datetime.utcnow() + timedelta(days=7)
        to_encode = {
            "exp": expire,
            "sub": email,
            "type": "email_verification",
            "iat": datetime.utcnow(),
        }
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


class MFAManager:
    """Multi-Factor Authentication management using TOTP"""

    @staticmethod
    def generate_secret() -> str:
        """Generate a new TOTP secret"""
        return pyotp.random_base32()

    @staticmethod
    def generate_qr_code(secret: str, user_email: str, issuer: str = None) -> str:
        """
        Generate QR code for authenticator app
        Returns base64 encoded SVG
        """
        if issuer is None:
            issuer = settings.APP_NAME

        totp = pyotp.TOTP(secret)
        uri = totp.provisioning_uri(
            name=user_email,
            issuer_name=issuer
        )

        # Generate QR code as SVG
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to base64 or return URI for client-side generation
        return uri

    @staticmethod
    def verify_totp(secret: str, token: str, window: int = 1) -> bool:
        """
        Verify TOTP token
        window: number of time steps to check on either side
        """
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=window)

    @staticmethod
    def get_current_totp(secret: str) -> str:
        """Get current TOTP token (for testing)"""
        totp = pyotp.TOTP(secret)
        return totp.now()


class EncryptionManager:
    """Data encryption for sensitive fields"""

    def __init__(self, key: Optional[str] = None):
        """Initialize with encryption key"""
        self.key = key or settings.ENCRYPTION_KEY
        if self.key:
            self.cipher = Fernet(self.key.encode() if isinstance(self.key, str) else self.key)
        else:
            self.cipher = None

    @staticmethod
    def generate_key() -> str:
        """Generate a new encryption key"""
        return Fernet.generate_key().decode()

    def encrypt(self, data: str) -> str:
        """Encrypt string data"""
        if not self.cipher:
            raise ValueError("Encryption key not configured")

        return self.cipher.encrypt(data.encode()).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt string data"""
        if not self.cipher:
            raise ValueError("Encryption key not configured")

        return self.cipher.decrypt(encrypted_data.encode()).decode()


class APIKeyManager:
    """Manage API keys for programmatic access"""

    @staticmethod
    def generate_api_key(prefix: str = "sk") -> str:
        """Generate a secure API key"""
        random_part = secrets.token_urlsafe(32)
        return f"{prefix}_{random_part}"

    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """Hash API key for storage"""
        return pwd_context.hash(api_key)

    @staticmethod
    def verify_api_key(plain_key: str, hashed_key: str) -> bool:
        """Verify API key against hash"""
        return pwd_context.verify(plain_key, hashed_key)


class CSRFManager:
    """CSRF token management"""

    @staticmethod
    def generate_csrf_token() -> str:
        """Generate CSRF token"""
        return secrets.token_urlsafe(32)

    @staticmethod
    def verify_csrf_token(token: str, expected_token: str) -> bool:
        """Verify CSRF token"""
        return secrets.compare_digest(token, expected_token)


# Global instances
password_manager = PasswordManager()
token_manager = TokenManager()
mfa_manager = MFAManager()
encryption_manager = EncryptionManager()
api_key_manager = APIKeyManager()
csrf_manager = CSRFManager()
password_validator = PasswordValidator()
