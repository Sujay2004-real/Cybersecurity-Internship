# Project 2: Web Application Vulnerability Scanner

## Overview
A Python-based security tool that actively probes a web application for common vulnerabilities including **SQL Injection**, **Cross-Site Scripting (XSS)**, and **missing HTTP Security Headers**.

---

## Features
- **SQL Injection Detection** — Error-based and boolean-based payload testing on URL params and HTML forms
- **XSS Detection** — Reflected XSS payload injection across URL params and forms
- **Security Header Analysis** — Checks for 7 critical HTTP security headers (CSP, HSTS, X-Frame-Options, etc.)
- **Threaded Scanning** — Non-blocking UI with stop-at-any-time support
- **Live Activity Log** — Real-time scan progress in a dedicated tab
- **Severity Ratings** — Critical / High / Medium per finding
- **Export Report** — Save findings to a `.txt` report file

---

## How to Use

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the GUI
```bash
cd 02-Web-App-Scanner
python src/gui.py
```

### 3. CLI mode
```bash
python src/scanner.py http://target-url.com?id=1
```

---

## Modules
| File | Purpose |
|---|---|
| `src/scanner.py` | Core scanning engine (SQLi, XSS, Headers) |
| `src/gui.py` | Dark-themed tkinter GUI |

---

## ⚠️ Disclaimer
This tool is for **educational purposes only**. Only scan applications you own or have explicit written permission to test. Unauthorized scanning is illegal.
