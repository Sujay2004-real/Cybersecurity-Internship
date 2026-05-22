# 04 — CryptoVault: Advanced Encryption Tool

A professional-grade encryption toolkit implementing industry-standard AES and RSA algorithms for secure data transmission and storage.  
**Folder 4 of 4** in the Cybersecurity Internship portfolio.

---

## Algorithms Implemented

| Algorithm | Use Case | Standard |
|---|---|---|
| **AES-256-GCM** | Symmetric encryption (text & files) | NIST FIPS 197 |
| **RSA-2048 / RSA-4096** | Asymmetric key management | PKCS#8 / RFC 3447 |
| **Hybrid RSA + AES** | Secure transmission envelope | Industry standard |
| **RSA-PSS / SHA-256** | Digital signatures | RFC 8017 |
| **PBKDF2-HMAC-SHA256** | Password-based key derivation | NIST SP 800-132 |
| **SHA-256/512/3, BLAKE2b** | Integrity hashing | NIST / RFC 7693 |

---

## GUI Theme

**Electric Cyan / Ice-Blue Vault** — deliberately distinct from:
- Project 01 (teal/navy)
- Project 02 (neon purple)
- Project 03 (amber/military)

Features an animated **vault combination-lock** header decoration and
a deep slate blue palette (`#00e5ff` on `#060d14`).

---

## Installation

```bash
pip install -r requirements.txt
```

Only one external dependency: `cryptography` (PyCA — industry standard).

---

## Usage

```bash
python src/gui.py
```

---

## Features by Tab

### 🔐 AES Cipher
- Password-based AES-256-GCM encryption/decryption
- PBKDF2-HMAC-SHA256 key derivation (480,000 iterations — OWASP 2023)
- 256-bit random salt, 96-bit GCM nonce per message
- Authenticated encryption (detects tampering)

### 🔑 RSA Key Manager
- Generate RSA-2048 or RSA-4096 key pairs
- Optional password protection for private keys (PKCS#8)
- Export/import PEM files
- SHA-256 public key fingerprint display
- Live key-load status indicators in header

### 📨 Hybrid (RSA + AES)
- Encrypt large data with recipient's public key
- Ephemeral AES-256-GCM session key per message
- RSA-OAEP key wrapping (SHA-256 mask)
- Only the holder of the matching private key can decrypt

### ✍ Digital Signatures
- Sign messages with RSA-PSS / SHA-256
- Verify signatures against a public key
- Detects any modification to signed data

### # Hash Utility
- Text hashing: SHA-256, SHA-512, SHA-384, SHA3-256, SHA3-512, MD5, BLAKE2b
- File hashing with size reporting
- One-click copy to clipboard

### 📁 File Crypto
- File encryption/decryption in both AES (password) and Hybrid (RSA) modes
- Reports input/output sizes and SHA-256 checksums

---

## Security Notes

- AES-GCM provides **authenticated encryption** — any tampering is detected
- RSA private keys never leave the application unless you explicitly save them
- PBKDF2 with 480,000 iterations provides strong brute-force resistance
- All random material (salt, nonce, session keys) uses `os.urandom()` (CSPRNG)

---

## Project Structure

```
04-Encryption-Tool/
├── src/
│   ├── gui.py             ← Main GUI application (6 tabs)
│   └── crypto_engine.py   ← Cryptographic backend
├── requirements.txt
└── README.md
```
