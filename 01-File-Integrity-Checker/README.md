# Project 1: File Integrity Checker

## Overview
This tool is a Python-based security utility designed to monitor the integrity of a specific file. It uses the **SHA-256 cryptographic hashing algorithm** to ensure that any unauthorized modification to the file is detected immediately.



## Features
* **Baseline Generation:** On the first run, the tool generates a "fingerprint" (hash) of the target file and stores it.
* **Integrity Verification:** On subsequent runs, it compares the current hash against the stored baseline.
* **Tamper Detection:** If even a single character in the file changes, the tool will alert the user that the integrity has been compromised.

## How to Use
1. **Navigate to the directory:**
   ```bash
   cd 01-File-Integrity-Checker
2. **Run the tool on a target file:**
   ```python src/checker.py yourfile.txt