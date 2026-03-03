import hashlib
import os
import sys

def calculate_sha256(filepath):
    """Calculates the SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            # Read in chunks to handle large files efficiently
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python checker.py <file_path>")
        return

    target_file = sys.argv[1]
    
    # 1. Check if file exists
    if not os.path.exists(target_file):
        print(f"[-] Error: File '{target_file}' not found.")
        return

    # 2. Calculate current hash
    current_hash = calculate_sha256(target_file)
    print(f"[*] File: {target_file}")
    print(f"[*] Current SHA-256: {current_hash}")

    # 3. Baseline Logic (Simple implementation)
    baseline_file = "baseline.txt"
    
    if not os.path.exists(baseline_file):
        # Create baseline if it doesn't exist
        with open(baseline_file, "w") as f:
            f.write(current_hash)
        print("[+] Baseline created and stored.")
    else:
        # Compare with existing baseline
        with open(baseline_file, "r") as f:
            stored_hash = f.read().strip()
        
        if current_hash == stored_hash:
            print("[V] Integrity Verified: No changes detected.")
        else:
            print("[!] WARNING: File has been modified or tampered with!")
            print(f"[!] Stored Hash:  {stored_hash}")
            print(f"[!] Current Hash: {current_hash}")

if __name__ == "__main__":
    main()