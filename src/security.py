import hashlib
import os


def hash_password(password: str) -> str:
    """Hash a password using SHA-256 with a random salt."""
    salt = os.urandom(16).hex()
    hashed = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}:{hashed}"


def verify_password(password: str, stored: str) -> bool:
    """Verify a password against a stored salt:hash string."""
    try:
        salt, hashed = stored.split(":", 1)
        return hashlib.sha256((salt + password).encode()).hexdigest() == hashed
    except Exception:
        return False


def is_hashed(stored: str) -> bool:
    """Check if a stored password is already hashed (has salt:hash format)."""
    parts = stored.split(":", 1)
    return len(parts) == 2 and len(parts[0]) == 32
