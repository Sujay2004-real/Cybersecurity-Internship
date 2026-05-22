# 🛡️ Cybersecurity Portfolio Workstation

Welcome to the **Cybersecurity Internship Portfolio** repository. This collection houses a suite of professional-grade, interactive security scanners, cryptographic engines, and system monitoring utilities developed during my security engineering internship. 

Every tool is fully realized, featuring modular architectures, rich graphical user interfaces, and robust security practices designed to showcase concepts in ethical hacking, system defense, and cryptography.

---

## 📂 Project Portfolio Index

All projects are fully completed and functional, showcasing distinct dark-mode GUI designs tailored to their operational profiles.

| # | Project Title | Primary Security Objective | Interface / Theme Profile | Quick Link |
| :--- | :--- | :--- | :--- | :--- |
| **01** | **File Integrity Checker** | Passive system defense & active baseline change detection. | *Navy & Teal Modern Console* | [View Project](./01-File-Integrity-Checker) |
| **02** | **Web App Scanner** | Active web vulnerability probing (SQLi, XSS, HTTP Headers). | *Neon Purple Dark-Mode GUI* (`#0f0a1e`) | [View Project](./02-Web-App-Scanner) |
| **03** | **NetRecon Toolkit** | Host sweeps, multi-threaded port scanning & banner grabbing. | *Amber Military CRT Radar Canvas* | [View Project](./03-Pentest-Toolkit) |
| **04** | **CryptoVault Workstation** | Industry-grade AES/RSA symmetric, asymmetric, and hybrid crypto. | *Electric Cyan Tech-Vault* (`#00e5ff`) | [View Project](./04-Encryption-Tool) |

---

## 🛠️ Consolidated Technology Stack

Across the suite of tools, the codebase utilizes modern Python libraries and custom graphical components:

* **Core Platform:** Python 3.10+
* **Cryptographic Standards:** PyCA `cryptography` (implementing AES-256-GCM, RSA-OAEP, RSA-PSS, PBKDF2-HMAC-SHA256)
* **System & Parsing:** Standard library `os`, `sys`, `hashlib`, `json`, `math`
* **Networking Modules:** Multi-threaded `socket` sockets, standard `requests` & `urllib3` engines
* **GUI Presentation:** Python `tkinter` + custom dynamic canvases (animated radar sweeps, grid heat-maps)
* **Concurrency:** `threading` module for background workers, maintaining fluid non-blocking interfaces

---

## 🚀 Portfolio Projects Spotlight & Run Instructions

### 01 🔍 File Integrity Checker
A security monitoring script designed to safeguard sensitive files against unauthorized modifications.
* **Cryptographic Baseline:** Computes a unique **SHA-256 signature** of the target file upon initiation.
* **Real-time Verification:** Flags and records exact tampering events if even a single character changes.
* **Command Line Run:**
  ```bash
  python 01-File-Integrity-Checker/src/checker.py <target-file-path>
  ```

### 02 🕸️ Web Application Scanner
An automated security scanner that actively tests web applications for critical injection points and server misconfigurations.
* **Dynamic Auditing:** Evaluates parameters and form endpoints for SQL Injection (SQLi) and Reflected Cross-Site Scripting (XSS).
* **Header Inspector:** Checks for the presence of 7 critical HTTP protection headers.
* **Interface Features:** Real-time log console, threat severity coloring, and custom text report exports.
* **Execution:**
  ```bash
  pip install -r 02-Web-App-Scanner/requirements.txt
  python 02-Web-App-Scanner/src/gui.py
  ```

### 03 📡 NetRecon Port Scanner & Subnet Sweeper
A concurrent network scanning workstation mimicking a retro military amber terminal.
* **Radar Sweep Engine:** An active visual radar widget indicating ongoing scan sweeps.
* **Port Heat-Map Grid:** Real-time visual display showing open and closed ports sorted by risk level.
* **Ping Sweeper:** Multi-threaded CIDR discovery tool to locate alive hosts on a local network.
* **Execution:**
  ```bash
  python 03-Pentest-Toolkit/src/gui.py
  ```

### 04 🔐 CryptoVault Advanced Cipher Suite
A robust hybrid cryptographic vault utilizing industry-standard high-performance algorithms.
* **Authenticated AES-256-GCM:** Text and file encryption featuring individual CSPRNG salts and GCM nonces.
* **RSA Key Management:** Generate 2048/4096-bit keypairs with PKCS#8 password protection.
* **Digital Signatures & Hashing:** RSA-PSS signature verification and raw hashing utilities supporting SHA-2, SHA-3, BLAKE2b, and MD5.
* **Execution:**
  ```bash
  pip install -r 04-Encryption-Tool/requirements.txt
  python 04-Encryption-Tool/src/gui.py
  ```

---

## 🔒 Safety & Professional Conduct

> [!WARNING]
> These applications were built strictly for educational, defensive, and authorized pentesting purposes. Under no circumstances should you run active scans (such as the Web Application Scanner or NetRecon Subnet Sweeper) against external environments without **prior written authorization** from the system owners. Unauthorized scanning or exploit attempts constitute a violation of cybersecurity laws.
