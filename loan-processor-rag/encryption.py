#!/usr/bin/env python3
"""
Encryption utilities for sensitive data
Uses Fernet (symmetric encryption) from cryptography library
"""

import os
from cryptography.fernet import Fernet
import base64

# Get encryption key from environment (32 bytes, base64 encoded)
# IMPORTANT: Set this in Railway environment variables!
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

if not ENCRYPTION_KEY:
    # Generate a key for local development (NOT for production!)
    print("⚠️  WARNING: No ENCRYPTION_KEY found in environment. Using temporary key.")
    print("⚠️  Set ENCRYPTION_KEY environment variable in Railway for production!")
    ENCRYPTION_KEY = Fernet.generate_key().decode()

# Create Fernet cipher
try:
    fernet = Fernet(ENCRYPTION_KEY.encode() if isinstance(ENCRYPTION_KEY, str) else ENCRYPTION_KEY)
except Exception as e:
    print(f"❌ Invalid ENCRYPTION_KEY: {e}")
    print("Generating new key...")
    ENCRYPTION_KEY = Fernet.generate_key().decode()
    fernet = Fernet(ENCRYPTION_KEY.encode())


def encrypt_field(plaintext: str) -> str:
    """
    Encrypt a string field
    Returns base64-encoded encrypted string
    """
    if not plaintext:
        return None

    try:
        encrypted_bytes = fernet.encrypt(plaintext.encode())
        return encrypted_bytes.decode()
    except Exception as e:
        print(f"Encryption error: {e}")
        return None


def decrypt_field(encrypted_text: str) -> str:
    """
    Decrypt a string field
    Returns original plaintext
    """
    if not encrypted_text:
        return None

    try:
        decrypted_bytes = fernet.decrypt(encrypted_text.encode())
        return decrypted_bytes.decode()
    except Exception as e:
        print(f"Decryption error: {e}")
        return None


def encrypt_file(file_path: str) -> bool:
    """
    Encrypt a file in place
    Returns True if successful
    """
    try:
        # Read file
        with open(file_path, 'rb') as f:
            file_data = f.read()

        # Encrypt
        encrypted_data = fernet.encrypt(file_data)

        # Write back
        with open(file_path, 'wb') as f:
            f.write(encrypted_data)

        return True
    except Exception as e:
        print(f"File encryption error: {e}")
        return False


def decrypt_file(file_path: str, output_path: str = None):
    """
    Decrypt a file
    If output_path is provided, writes to that path and returns True/False
    If output_path is None, returns the decrypted bytes
    """
    try:
        # Read encrypted file
        with open(file_path, 'rb') as f:
            encrypted_data = f.read()

        # Decrypt
        decrypted_data = fernet.decrypt(encrypted_data)

        # If output path specified, write to file
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(decrypted_data)
            return True

        # Otherwise return the decrypted bytes
        return decrypted_data

    except Exception as e:
        print(f"File decryption error: {e}")
        return None


def generate_encryption_key() -> str:
    """
    Generate a new encryption key
    Use this to create ENCRYPTION_KEY for Railway
    """
    key = Fernet.generate_key()
    return key.decode()


if __name__ == "__main__":
    # Generate a new key for production use
    print("=== Encryption Key Generator ===")
    print("\nGenerated Encryption Key (save this securely!):")
    print(generate_encryption_key())
    print("\n⚠️  Add this to Railway as environment variable 'ENCRYPTION_KEY'")
    print("⚠️  NEVER commit this key to git or share it publicly!")
