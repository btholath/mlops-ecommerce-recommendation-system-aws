"""
encryption_service.py
~~~~~~~~~~~~~~~~~~~~~

Self-contained utilities for symmetric (AES-256/Fernet) and asymmetric
(RSA-2048) encryption, suitable for protecting sensitive data in transit
and at rest.

Usage examples are shown in the ``__main__`` block.  The module logs to
``security.encryption``; tweak the root log-level in your application
bootstrap if you want less (or more) verbosity.
"""
from __future__ import annotations

import base64
import json
import logging
import os
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

_LOG = logging.getLogger("security.encryption")


# --------------------------------------------------------------------------- #
# Symmetric encryption (Fernet/AES-256)                                        #
# --------------------------------------------------------------------------- #
class SymmetricEncryptor:
    """Encrypt/Decrypt small blobs or files with a key derived from *password*.

    Parameters
    ----------
    password
        If *None*, the constructor falls back to the ``ENCRYPTION_PASSWORD``
        environment variable.  A ``ValueError`` is raised when neither are set.
    salt
        Optional salt (bytes).  In production you **must** generate and persist
        a random salt – hard-coding is only acceptable in demos.
    """

    def __init__(self, password: str | None = None, *, salt: bytes | None = None) -> None:
        if password is None:
            password = os.getenv("ENCRYPTION_PASSWORD")

        if not password:
            raise ValueError("An encryption password is required")

        self._key = self._derive_key(password.encode(), salt or b"salt_1234567890")
        self._fernet = Fernet(self._key)

        _LOG.debug("SymmetricEncryptor initialised (salt length = %d)", len(salt or b"salt_1234567890"))

    # --------------------------------------------------------------------- #
    # Public helpers                                                        #
    # --------------------------------------------------------------------- #
    def encrypt(self, data: str | bytes | dict[str, Any]) -> str:
        """Encrypt *data* and return a base64-encoded ciphertext string."""
        try:
            if isinstance(data, dict):
                data = json.dumps(data)

            plaintext = data.encode() if isinstance(data, str) else data
            token = self._fernet.encrypt(plaintext)
            _LOG.info("Data encrypted (%d bytes → %d bytes)", len(plaintext), len(token))
            return base64.urlsafe_b64encode(token).decode()
        except Exception:
            _LOG.exception("Encryption failed")
            raise

    def decrypt(self, token_b64: str) -> str:
        """Decrypt *token_b64* (str) and return the original plaintext (str)."""
        try:
            token = base64.urlsafe_b64decode(token_b64.encode())
            plaintext = self._fernet.decrypt(token)
            _LOG.info("Data decrypted (%d bytes)", len(plaintext))
            return plaintext.decode()
        except Exception:
            _LOG.exception("Decryption failed")
            raise

    def encrypt_file(self, infile: os.PathLike | str, outfile: os.PathLike | str | None = None) -> Path:
        """Encrypt the contents of *infile* → *outfile* (``.encrypted`` suffix by default)."""
        infile = Path(infile)
        outfile = Path(outfile) if outfile else infile.with_suffix(infile.suffix + ".encrypted")

        try:
            plaintext = infile.read_bytes()
            ciphertext = self._fernet.encrypt(plaintext)
            outfile.write_bytes(ciphertext)
            _LOG.info("File encrypted: %s  →  %s", infile, outfile)
            return outfile
        except Exception:
            _LOG.exception("File encryption failed")
            raise

    def decrypt_file(self, infile: os.PathLike | str, outfile: os.PathLike | str | None = None) -> Path:
        """Decrypt *infile* (must be encrypted) → *outfile* (suffix stripped by default)."""
        infile = Path(infile)
        outfile = Path(outfile) if outfile else infile.with_suffix("")

        try:
            ciphertext = infile.read_bytes()
            plaintext = self._fernet.decrypt(ciphertext)
            outfile.write_bytes(plaintext)
            _LOG.info("File decrypted: %s  →  %s", infile, outfile)
            return outfile
        except Exception:
            _LOG.exception("File decryption failed")
            raise

    # --------------------------------------------------------------------- #
    # Internals                                                             #
    # --------------------------------------------------------------------- #
    @staticmethod
    def _derive_key(password: bytes, salt: bytes) -> bytes:
        """PBKDF2-HMAC-SHA256 ⇒ 32-byte Fernet key."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100_000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password))


# --------------------------------------------------------------------------- #
# Asymmetric encryption (RSA-2048)                                            #
# --------------------------------------------------------------------------- #
class AsymmetricEncryptor:
    """Utility wrapper for basic RSA key-pair generation and ciphertext handling."""

    def __init__(self, key_size: int = 2048) -> None:
        self._private_key: rsa.RSAPrivateKey | None = None
        self._public_key: rsa.RSAPublicKey | None = None
        self.key_size = key_size

    # --------------------------------------------------------------------- #
    # Key management                                                        #
    # --------------------------------------------------------------------- #
    def generate_key_pair(self) -> tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]:
        self._private_key = rsa.generate_private_key(public_exponent=65_537, key_size=self.key_size)
        self._public_key = self._private_key.public_key()
        _LOG.info("RSA-%d key-pair generated", self.key_size)
        return self._private_key, self._public_key

    def save_key_pair(
        self,
        priv_path: os.PathLike | str,
        pub_path: os.PathLike | str,
        *,
        password: str | None = None,
    ) -> None:
        if not (self._private_key and self._public_key):
            raise RuntimeError("Generate a key-pair first with generate_key_pair()")

        priv_alg = (
            serialization.BestAvailableEncryption(password.encode())
            if password
            else serialization.NoEncryption()
        )

        priv_pem = self._private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=priv_alg,
        )
        pub_pem = self._public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        Path(priv_path).write_bytes(priv_pem)
        Path(pub_path).write_bytes(pub_pem)
        _LOG.info("Keys written to %s , %s", priv_path, pub_path)

    # --------------------------------------------------------------------- #
    # Encrypt / Decrypt                                                     #
    # --------------------------------------------------------------------- #
    @staticmethod
    def encrypt(plaintext: str, public_key: rsa.RSAPublicKey) -> str:
        """Encrypt *plaintext* with *public_key* using OAEP→base64."""
        ciphertext = public_key.encrypt(
            plaintext.encode(),
            padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
        )
        _LOG.debug("Asymmetric encryption complete (%d bytes)", len(ciphertext))
        return base64.b64encode(ciphertext).decode()

    def decrypt(self, ciphertext_b64: str) -> str:
        """Decrypt *ciphertext_b64* with the instance’s private key."""
        if not self._private_key:
            raise RuntimeError("Private key not initialised – call generate_key_pair() first")

        plaintext = self._private_key.decrypt(
            base64.b64decode(ciphertext_b64),
            padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
        )
        _LOG.debug("Asymmetric decryption complete (%d bytes)", len(plaintext))
        return plaintext.decode()


# --------------------------------------------------------------------------- #
# Simple demo (only runs when the file is executed directly)                 #
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s  %(message)s")

    # --- Symmetric ------------------------------------------------------- #
    encryptor = SymmetricEncryptor("MyS3cretPassw0rd!")

    sample = {"cc": "4111-1111-1111-1111", "api": "sk-abc123"}
    cipher = encryptor.encrypt(sample)
    plain = encryptor.decrypt(cipher)
    _LOG.info("Round-trip OK?  %s", plain == json.dumps(sample))

    # --- Asymmetric ------------------------------------------------------ #
    asym = AsymmetricEncryptor()
    priv, pub = asym.generate_key_pair()

    secret_msg = "Hello—this is classified."
    cipher2 = asym.encrypt(secret_msg, pub)
    plain2 = asym.decrypt(cipher2)
    _LOG.info("Asymmetric round-trip OK?  %s", secret_msg == plain2)
