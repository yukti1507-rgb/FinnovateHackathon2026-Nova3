from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from cryptography.fernet import Fernet, InvalidToken
import streamlit as st


# ============================================================
# ENCRYPTION
# ============================================================

def get_encryption_key():
    """
    Retrieves the Fernet encryption key from Streamlit secrets.

    The key should be stored in:
        .streamlit/secrets.toml

    The key must NOT be stored in the SQLite database
    or hard-coded in the source code.
    """

    try:
        key = st.secrets["FINANCE_ENCRYPTION_KEY"]
    except KeyError as e:
        raise RuntimeError(
            "FINANCE_ENCRYPTION_KEY was not found in Streamlit secrets."
        ) from e

    if not key:
        raise RuntimeError(
            "FINANCE_ENCRYPTION_KEY is empty."
        )

    return key


def get_cipher():
    """
    Creates a Fernet cipher using the application's
    encryption key.
    """

    key = get_encryption_key()

    try:
        return Fernet(key.encode("utf-8"))
    except Exception as e:
        raise RuntimeError(
            "FINANCE_ENCRYPTION_KEY is not a valid Fernet key."
        ) from e


# ============================================================
# MONEY CONVERSION
# ============================================================

def to_cents(amount):
    """
    Converts a monetary amount into integer cents.

    Examples:
        1250.50 -> 125050
        "1250.50" -> 125050
        500 -> 50000

    Decimal is used instead of float to avoid
    floating-point rounding problems.
    """

    try:
        decimal_amount = Decimal(str(amount))
    except (InvalidOperation, ValueError, TypeError) as e:
        raise ValueError(
            "Invalid monetary amount."
        ) from e

    decimal_amount = decimal_amount.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )

    if decimal_amount < 0:
        raise ValueError(
            "Monetary amount cannot be negative."
        )

    cents = int(
        decimal_amount * Decimal("100")
    )

    return cents


def from_cents(cents):
    """
    Converts integer cents into a Decimal monetary amount.

    Example:
        125050 -> Decimal("1250.50")
    """

    try:
        cents = int(cents)
    except (TypeError, ValueError) as e:
        raise ValueError(
            "Invalid cents value."
        ) from e

    return (
        Decimal(cents) / Decimal("100")
    ).quantize(
        Decimal("0.01")
    )


# ============================================================
# ENCRYPTION OF MONETARY VALUES
# ============================================================

def encrypt_amount(amount):
    """
    Converts a monetary amount into integer cents,
    then encrypts the cents.

    Example:

        1250.50
            ↓
        125050
            ↓
        encrypted TEXT
    """

    cents = to_cents(amount)

    cipher = get_cipher()

    encrypted = cipher.encrypt(
        str(cents).encode("utf-8")
    )

    return encrypted.decode("utf-8")


def decrypt_amount(encrypted_amount):
    """
    Decrypts an encrypted monetary value and returns
    the value as integer cents.

    Example:

        encrypted TEXT
            ↓
        125050
    """

    if encrypted_amount is None:
        return None

    if encrypted_amount == "":
        return None

    cipher = get_cipher()

    try:
        decrypted = cipher.decrypt(
            encrypted_amount.encode("utf-8")
        )

        cents = int(
            decrypted.decode("utf-8")
        )

    except (InvalidToken, ValueError, TypeError) as e:
        raise ValueError(
            "Unable to decrypt financial amount."
        ) from e

    return cents


def decrypt_amount_decimal(encrypted_amount):
    """
    Decrypts an encrypted monetary value and returns
    it as a Decimal.

    Example:

        encrypted TEXT
            ↓
        Decimal("1250.50")
    """

    cents = decrypt_amount(encrypted_amount)

    if cents is None:
        return None

    return from_cents(cents)