"""
Advanced Encryption Tool — Cryptographic Engine
Implements:
  • AES-256-GCM  (authenticated symmetric encryption)
  • RSA-2048 / RSA-4096  (asymmetric key exchange & signing)
  • RSA + AES Hybrid  (secure data transmission envelope)
  • Password-Based Key Derivation  (PBKDF2-HMAC-SHA256)
  • Digital Signatures  (RSA-PSS with SHA-256)
  • File Encryption / Decryption

All operations use the Python standard library (hashlib, hmac, os, struct)
plus the 'cryptography' package for production-grade primitives.
"""

import os
import json
import struct
import hashlib
import hmac
import base64
from datetime import datetime
from pathlib import Path
from typing import Tuple

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.asymmetric import rsa, padding as asym_padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidTag, InvalidSignature

# ── Constants ─────────────────────────────────────────────────────────────────

AES_KEY_BITS   = 256          # AES-256
AES_NONCE_LEN  = 12           # GCM standard nonce
AES_TAG_LEN    = 16           # GCM authentication tag
PBKDF2_ITERS   = 480_000      # OWASP 2023 recommendation
SALT_LEN       = 32           # 256-bit salt

MAGIC_AES      = b"AESCRYPT1"  # 9-byte file magic
MAGIC_HYBRID   = b"HYBRIDV1 "  # 9-byte hybrid file magic

# ══════════════════════════════════════════════════════════════════════════════
#  UTILITIES
# ══════════════════════════════════════════════════════════════════════════════

def to_b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")

def from_b64(s: str) -> bytes:
    return base64.b64decode(s.encode("ascii"))

def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def sha512_hex(data: bytes) -> str:
    return hashlib.sha512(data).hexdigest()

def secure_random(n: int) -> bytes:
    return os.urandom(n)

def format_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


# ══════════════════════════════════════════════════════════════════════════════
#  AES-256-GCM  (Password-Based)
# ══════════════════════════════════════════════════════════════════════════════

class AESCipher:
    """
    AES-256-GCM symmetric encryption.
    Key derivation: PBKDF2-HMAC-SHA256 with random 256-bit salt.
    Output format (binary):
      MAGIC(9) | SALT(32) | NONCE(12) | CIPHERTEXT+TAG
    """

    @staticmethod
    def derive_key(password: str, salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=PBKDF2_ITERS,
            backend=default_backend(),
        )
        return kdf.derive(password.encode("utf-8"))

    @classmethod
    def encrypt(cls, plaintext: bytes, password: str) -> bytes:
        salt  = secure_random(SALT_LEN)
        nonce = secure_random(AES_NONCE_LEN)
        key   = cls.derive_key(password, salt)
        aesgcm = AESGCM(key)
        ct_tag = aesgcm.encrypt(nonce, plaintext, None)
        return MAGIC_AES + salt + nonce + ct_tag

    @classmethod
    def decrypt(cls, blob: bytes, password: str) -> bytes:
        if not blob.startswith(MAGIC_AES):
            raise ValueError("Not a valid AES-encrypted blob (bad magic).")
        offset    = len(MAGIC_AES)
        salt      = blob[offset: offset + SALT_LEN];  offset += SALT_LEN
        nonce     = blob[offset: offset + AES_NONCE_LEN]; offset += AES_NONCE_LEN
        ct_tag    = blob[offset:]
        key       = cls.derive_key(password, salt)
        aesgcm    = AESGCM(key)
        try:
            return aesgcm.decrypt(nonce, ct_tag, None)
        except InvalidTag:
            raise ValueError("Decryption failed — wrong password or data corrupted.")

    @classmethod
    def encrypt_text(cls, text: str, password: str) -> str:
        blob = cls.encrypt(text.encode("utf-8"), password)
        return to_b64(blob)

    @classmethod
    def decrypt_text(cls, b64_blob: str, password: str) -> str:
        blob = from_b64(b64_blob)
        return cls.decrypt(blob, password).decode("utf-8")

    @classmethod
    def encrypt_file(cls, src: str, dst: str, password: str) -> dict:
        data = Path(src).read_bytes()
        blob = cls.encrypt(data, password)
        Path(dst).write_bytes(blob)
        return {
            "input_file":  src,
            "output_file": dst,
            "input_size":  format_size(len(data)),
            "output_size": format_size(len(blob)),
            "sha256_input": sha256_hex(data),
            "algorithm":   "AES-256-GCM",
            "kdf":         f"PBKDF2-HMAC-SHA256 ({PBKDF2_ITERS:,} iterations)",
        }

    @classmethod
    def decrypt_file(cls, src: str, dst: str, password: str) -> dict:
        blob = Path(src).read_bytes()
        data = cls.decrypt(blob, password)
        Path(dst).write_bytes(data)
        return {
            "input_file":  src,
            "output_file": dst,
            "output_size": format_size(len(data)),
            "sha256_output": sha256_hex(data),
            "algorithm":   "AES-256-GCM",
        }


# ══════════════════════════════════════════════════════════════════════════════
#  RSA KEY MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════

class RSAKeyPair:
    """RSA-2048 or RSA-4096 key pair generation and management."""

    def __init__(self, key_size: int = 2048):
        self.key_size   = key_size
        self._private   = None
        self._public    = None

    @property
    def private_key(self):
        return self._private

    @property
    def public_key(self):
        return self._public

    def generate(self, progress_cb=None):
        if progress_cb:
            progress_cb(f"Generating RSA-{self.key_size} key pair…")
        self._private = rsa.generate_private_key(
            public_exponent=65537,
            key_size=self.key_size,
            backend=default_backend(),
        )
        self._public = self._private.public_key()
        if progress_cb:
            progress_cb(f"RSA-{self.key_size} key pair generated ✔")

    def export_private_pem(self, password: str | None = None) -> str:
        enc = (
            serialization.BestAvailableEncryption(password.encode())
            if password else serialization.NoEncryption()
        )
        return self._private.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=enc,
        ).decode("ascii")

    def export_public_pem(self) -> str:
        return self._public.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("ascii")

    def export_public_fingerprint(self) -> str:
        der = self._public.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        digest = hashlib.sha256(der).hexdigest()
        return ":".join(digest[i:i+4] for i in range(0, 32, 4))

    @classmethod
    def load_private_pem(cls, pem_text: str, password: str | None = None) -> "RSAKeyPair":
        pw = password.encode() if password else None
        key = serialization.load_pem_private_key(
            pem_text.encode("ascii"), password=pw, backend=default_backend()
        )
        obj = cls(key.key_size)
        obj._private = key
        obj._public  = key.public_key()
        return obj

    @classmethod
    def load_public_pem(cls, pem_text: str) -> "RSAKeyPair":
        key = serialization.load_pem_public_key(
            pem_text.encode("ascii"), backend=default_backend()
        )
        obj = cls(key.key_size)
        obj._public = key
        return obj

    def save_private(self, path: str, password: str | None = None):
        Path(path).write_text(self.export_private_pem(password))

    def save_public(self, path: str):
        Path(path).write_text(self.export_public_pem())


# ══════════════════════════════════════════════════════════════════════════════
#  RSA ENCRYPT / DECRYPT  (small data — OAEP)
# ══════════════════════════════════════════════════════════════════════════════

class RSACipher:
    """RSA-OAEP encryption (for small payloads, typically AES keys)."""

    _PADDING = asym_padding.OAEP(
        mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None,
    )

    @classmethod
    def encrypt(cls, plaintext: bytes, public_key) -> bytes:
        return public_key.encrypt(plaintext, cls._PADDING)

    @classmethod
    def decrypt(cls, ciphertext: bytes, private_key) -> bytes:
        return private_key.decrypt(ciphertext, cls._PADDING)

    @classmethod
    def encrypt_text(cls, text: str, public_key) -> str:
        data = text.encode("utf-8")
        if len(data) > 190:
            raise ValueError(
                "RSA-OAEP can only encrypt ≤190 bytes directly.\n"
                "Use Hybrid (RSA+AES) for larger data."
            )
        return to_b64(cls.encrypt(data, public_key))

    @classmethod
    def decrypt_text(cls, b64_ct: str, private_key) -> str:
        return cls.decrypt(from_b64(b64_ct), private_key).decode("utf-8")


# ══════════════════════════════════════════════════════════════════════════════
#  HYBRID RSA + AES  (for large data / file transmission)
# ══════════════════════════════════════════════════════════════════════════════

class HybridCipher:
    """
    Industry-standard hybrid encryption envelope:
      1. Generate ephemeral AES-256 session key
      2. Encrypt data with AES-256-GCM
      3. Encrypt AES key with recipient's RSA public key (OAEP)

    Wire format (binary):
      MAGIC(9) | KEY_LEN(4, big-endian) | ENC_AES_KEY | NONCE(12) | CT+TAG
    """

    @classmethod
    def encrypt(cls, plaintext: bytes, public_key) -> bytes:
        aes_key   = secure_random(32)       # ephemeral AES-256 key
        nonce     = secure_random(AES_NONCE_LEN)
        aesgcm    = AESGCM(aes_key)
        ct_tag    = aesgcm.encrypt(nonce, plaintext, None)
        enc_key   = RSACipher.encrypt(aes_key, public_key)
        key_len   = struct.pack(">I", len(enc_key))
        return MAGIC_HYBRID + key_len + enc_key + nonce + ct_tag

    @classmethod
    def decrypt(cls, blob: bytes, private_key) -> bytes:
        if not blob.startswith(MAGIC_HYBRID):
            raise ValueError("Not a valid Hybrid-encrypted blob (bad magic).")
        offset    = len(MAGIC_HYBRID)
        key_len   = struct.unpack(">I", blob[offset: offset+4])[0]; offset += 4
        enc_key   = blob[offset: offset + key_len]; offset += key_len
        nonce     = blob[offset: offset + AES_NONCE_LEN]; offset += AES_NONCE_LEN
        ct_tag    = blob[offset:]
        aes_key   = RSACipher.decrypt(enc_key, private_key)
        aesgcm    = AESGCM(aes_key)
        try:
            return aesgcm.decrypt(nonce, ct_tag, None)
        except InvalidTag:
            raise ValueError("Hybrid decryption failed — wrong key or corrupted data.")

    @classmethod
    def encrypt_text(cls, text: str, public_key) -> str:
        return to_b64(cls.encrypt(text.encode("utf-8"), public_key))

    @classmethod
    def decrypt_text(cls, b64_blob: str, private_key) -> str:
        return cls.decrypt(from_b64(b64_blob), private_key).decode("utf-8")

    @classmethod
    def encrypt_file(cls, src: str, dst: str, public_key) -> dict:
        data = Path(src).read_bytes()
        blob = cls.encrypt(data, public_key)
        Path(dst).write_bytes(blob)
        return {
            "input_file":  src,
            "output_file": dst,
            "input_size":  format_size(len(data)),
            "output_size": format_size(len(blob)),
            "sha256_input": sha256_hex(data),
            "algorithm":   "Hybrid RSA-OAEP + AES-256-GCM",
        }

    @classmethod
    def decrypt_file(cls, src: str, dst: str, private_key) -> dict:
        blob = Path(src).read_bytes()
        data = cls.decrypt(blob, private_key)
        Path(dst).write_bytes(data)
        return {
            "input_file":  src,
            "output_file": dst,
            "output_size": format_size(len(data)),
            "sha256_output": sha256_hex(data),
            "algorithm":   "Hybrid RSA-OAEP + AES-256-GCM",
        }


# ══════════════════════════════════════════════════════════════════════════════
#  DIGITAL SIGNATURES  (RSA-PSS)
# ══════════════════════════════════════════════════════════════════════════════

class DigitalSigner:
    """RSA-PSS signatures with SHA-256."""

    _PADDING = asym_padding.PSS(
        mgf=asym_padding.MGF1(hashes.SHA256()),
        salt_length=asym_padding.PSS.MAX_LENGTH,
    )
    _HASH = hashes.SHA256()

    @classmethod
    def sign(cls, data: bytes, private_key) -> bytes:
        return private_key.sign(data, cls._PADDING, cls._HASH)

    @classmethod
    def verify(cls, data: bytes, signature: bytes, public_key) -> bool:
        try:
            public_key.verify(signature, data, cls._PADDING, cls._HASH)
            return True
        except InvalidSignature:
            return False

    @classmethod
    def sign_text(cls, text: str, private_key) -> str:
        return to_b64(cls.sign(text.encode("utf-8"), private_key))

    @classmethod
    def verify_text(cls, text: str, b64_sig: str, public_key) -> bool:
        return cls.verify(text.encode("utf-8"), from_b64(b64_sig), public_key)

    @classmethod
    def sign_file(cls, path: str, private_key) -> dict:
        data = Path(path).read_bytes()
        sig  = cls.sign(data, private_key)
        sig_path = path + ".sig"
        Path(sig_path).write_bytes(sig)
        return {
            "file":        path,
            "sig_file":    sig_path,
            "sha256":      sha256_hex(data),
            "sig_b64":     to_b64(sig)[:64] + "…",
            "algorithm":   "RSA-PSS / SHA-256",
        }

    @classmethod
    def verify_file(cls, path: str, sig_path: str, public_key) -> dict:
        data = Path(path).read_bytes()
        sig  = Path(sig_path).read_bytes()
        valid = cls.verify(data, sig, public_key)
        return {
            "file":    path,
            "sha256":  sha256_hex(data),
            "valid":   valid,
            "result":  "✔  SIGNATURE VALID" if valid else "✘  SIGNATURE INVALID",
        }


# ══════════════════════════════════════════════════════════════════════════════
#  HASH / CHECKSUM UTILITY
# ══════════════════════════════════════════════════════════════════════════════

class Hasher:
    ALGORITHMS = {
        "SHA-256":  hashlib.sha256,
        "SHA-512":  hashlib.sha512,
        "SHA-384":  hashlib.sha384,
        "SHA3-256": hashlib.sha3_256,
        "SHA3-512": hashlib.sha3_512,
        "MD5":      hashlib.md5,
        "BLAKE2b":  lambda: hashlib.blake2b(),
    }

    @classmethod
    def hash_text(cls, text: str, algorithm: str = "SHA-256") -> str:
        h = cls.ALGORITHMS[algorithm]()
        h.update(text.encode("utf-8"))
        return h.hexdigest()

    @classmethod
    def hash_file(cls, path: str, algorithm: str = "SHA-256") -> dict:
        h = cls.ALGORITHMS[algorithm]()
        size = 0
        with open(path, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
                size += len(chunk)
        return {
            "file":      path,
            "algorithm": algorithm,
            "digest":    h.hexdigest(),
            "size":      format_size(size),
        }
