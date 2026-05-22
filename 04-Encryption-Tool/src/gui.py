"""
Advanced Encryption Tool — GUI
Theme: Electric Cyan / Ice-Blue on Deep Slate — "Cryptographic Vault"
Unique from:
  01 → teal/navy      02 → neon purple      03 → amber/military

Layout:
  Header (vault door motif) → Tab ribbon → Tab content → Status bar

Tabs:
  🔐 AES Encrypt/Decrypt  |  🔑 RSA Key Manager
  📨 Hybrid (RSA+AES)     |  ✍  Digital Signature
  #  Hash Utility         |  📁 File Crypto
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import math
from datetime import datetime
from pathlib import Path

from crypto_engine import (
    AESCipher, RSACipher, RSAKeyPair, HybridCipher,
    DigitalSigner, Hasher, sha256_hex, to_b64, from_b64
)

# ══════════════════════════════════════════════════════════════════════════════
#  COLOUR PALETTE  —  Electric Cyan / Ice-Blue Vault
# ══════════════════════════════════════════════════════════════════════════════

BG       = "#060d14"   # deep blue-black
PANEL    = "#0b1520"   # dark navy panel
CARD     = "#0f1e2e"   # card surface
CARD2    = "#132433"   # slightly lighter
BORDER   = "#1a3347"   # steel-blue border
CYAN     = "#00e5ff"   # electric cyan (primary)
CYAN2    = "#80f0ff"   # bright ice cyan
CYAN_DK  = "#006080"   # muted cyan
ICE      = "#b2ebf2"   # ice white
BLUE     = "#1565c0"   # deep blue accent
BLUE_LT  = "#42a5f5"   # light blue
GREEN    = "#00e676"   # success green
RED      = "#ff1744"   # error red
ORANGE   = "#ff9100"   # warning orange
YELLOW   = "#ffe57f"   # info yellow
TEXT     = "#cce8f4"   # cool off-white
MUTED    = "#2e5266"   # muted slate
DIM      = "#1a3347"   # very dim

MF    = ("Courier New", 10)
MF_B  = ("Courier New", 10, "bold")
MF_T  = ("Courier New", 16, "bold")
MF_S  = ("Courier New",  9)
MF_XS = ("Courier New",  8)
SF    = ("Segoe UI",  10)
SF_B  = ("Segoe UI",  10, "bold")
SF_H  = ("Segoe UI",  12, "bold")

# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS & SHARED WIDGETS
# ══════════════════════════════════════════════════════════════════════════════

def _lt(c, a=20):
    r,g,b = int(c[1:3],16),int(c[3:5],16),int(c[5:7],16)
    return f"#{min(255,r+a):02x}{min(255,g+a):02x}{min(255,b+a):02x}"

def _dk(c, a=20):
    r,g,b = int(c[1:3],16),int(c[3:5],16),int(c[5:7],16)
    return f"#{max(0,r-a):02x}{max(0,g-a):02x}{max(0,b-a):02x}"

def cyan_btn(parent, text, cmd, bg=CYAN_DK, fg=CYAN2, w=None, **kw):
    extra = {"width": w} if w else {}
    b = tk.Button(parent, text=text, command=cmd,
                  bg=bg, fg=fg,
                  activebackground=_lt(bg,30), activeforeground=CYAN2,
                  font=MF_B, relief="flat", padx=10, pady=6,
                  cursor="hand2", bd=0, **extra, **kw)
    b.bind("<Enter>", lambda e: b.config(bg=_lt(bg,30)))
    b.bind("<Leave>", lambda e: b.config(bg=bg))
    return b

def section_label(parent, text: str, bg=CARD):
    row = tk.Frame(parent, bg=bg)
    row.pack(fill="x", pady=(10, 2))
    tk.Frame(row, bg=CYAN_DK, height=1).pack(fill="x", side="bottom")
    tk.Label(row, text=text, font=MF_B, bg=bg, fg=CYAN_DK).pack(side="left")
    return row

def text_area(parent, height=6, bg=PANEL, fg=TEXT, **kw):
    frm = tk.Frame(parent, bg=BORDER, highlightthickness=0)
    frm.pack(fill="x", **kw)
    t = tk.Text(frm, height=height, bg=bg, fg=fg,
                insertbackground=CYAN, font=MF,
                relief="flat", wrap="word", padx=8, pady=6,
                selectbackground=CYAN_DK, selectforeground=CYAN2)
    sb = ttk.Scrollbar(frm, orient="vertical", command=t.yview)
    t.configure(yscrollcommand=sb.set)
    t.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")
    return t

def entry_row(parent, label: str, var: tk.StringVar, show=None,
              bg=CARD, width=40):
    row = tk.Frame(parent, bg=bg)
    row.pack(fill="x", pady=2)
    tk.Label(row, text=label, font=MF_S, bg=bg,
             fg=MUTED, width=18, anchor="w").pack(side="left")
    kw = {"show": show} if show else {}
    e = tk.Entry(row, textvariable=var, width=width, bg=PANEL,
                 fg=CYAN2, insertbackground=CYAN, font=MF,
                 relief="flat", bd=6,
                 highlightbackground=BORDER, highlightthickness=1, **kw)
    e.pack(side="left", fill="x", expand=True, padx=(6, 0))
    return e

def result_strip(parent, bg=CARD):
    """A coloured result bar (hidden until used)."""
    frm = tk.Frame(parent, bg=bg, pady=5, padx=10)
    lbl = tk.Label(frm, text="", font=MF_S, bg=bg,
                   fg=GREEN, anchor="w", wraplength=740, justify="left")
    lbl.pack(fill="x")
    return frm, lbl


# ══════════════════════════════════════════════════════════════════════════════
#  ANIMATED VAULT LOCK CANVAS  (header decoration)
# ══════════════════════════════════════════════════════════════════════════════

class VaultLock(tk.Canvas):
    """Spinning combination-lock ring animation for the header."""
    W, H = 70, 70

    def __init__(self, parent, **kw):
        super().__init__(parent, width=self.W, height=self.H,
                         bg=PANEL, highlightthickness=0, **kw)
        self._angle = 0
        self._ticks = 0
        self._draw()
        self._animate()

    def _draw(self):
        self.delete("all")
        cx, cy = self.W // 2, self.H // 2
        R = cx - 4

        # Outer ring
        self.create_oval(cx-R, cy-R, cx+R, cy+R,
                         outline=CYAN_DK, width=2)
        # Ticks (combination dial)
        for i in range(40):
            deg = self._angle + i * 9
            rad = math.radians(deg)
            inner = R - (7 if i % 5 == 0 else 4)
            x1 = cx + R * math.cos(rad)
            y1 = cy + R * math.sin(rad)
            x2 = cx + inner * math.cos(rad)
            y2 = cy + inner * math.sin(rad)
            col = CYAN if i % 5 == 0 else CYAN_DK
            self.create_line(x1,y1,x2,y2, fill=col, width=1)

        # Inner gears (decorative)
        for off, col in [(12, BORDER), (8, CYAN_DK), (4, CYAN)]:
            self.create_oval(cx-off, cy-off, cx+off, cy+off,
                             outline=col, width=1)

        # Lock shackle hint
        for i in range(8):
            deg = -self._angle * 1.5 + i * 45
            rad = math.radians(deg)
            x = cx + 5 * math.cos(rad)
            y = cy + 5 * math.sin(rad)
            self.create_oval(x-1, y-1, x+1, y+1, fill=CYAN, outline="")

        # Center dot
        self.create_oval(cx-2,cy-2,cx+2,cy+2, fill=CYAN2, outline="")

    def _animate(self):
        self._angle = (self._angle + 1.2) % 360
        self._draw()
        self.after(30, self._animate)


# ══════════════════════════════════════════════════════════════════════════════
#  KEY STATE INDICATOR
# ══════════════════════════════════════════════════════════════════════════════

class KeyIndicator(tk.Frame):
    """Shows whether RSA keys are loaded."""

    def __init__(self, parent, label: str, **kw):
        super().__init__(parent, bg=CARD, **kw)
        self._dot = tk.Label(self, text="●", font=MF_B, bg=CARD, fg=MUTED)
        self._dot.pack(side="left")
        tk.Label(self, text=label, font=MF_XS, bg=CARD, fg=MUTED).pack(side="left", padx=2)

    def set_loaded(self, loaded: bool, label: str = ""):
        self._dot.config(fg=GREEN if loaded else MUTED)
        if label:
            self._dot.master.winfo_children()[1].config(  # type: ignore
                text=label, fg=GREEN if loaded else MUTED)


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN APPLICATION
# ══════════════════════════════════════════════════════════════════════════════

class EncryptionApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CryptoVault — Advanced Encryption Tool")
        self.geometry("1150x820")
        self.minsize(1000, 720)
        self.configure(bg=BG)

        # Key store
        self._key_pair: RSAKeyPair | None = None
        self._pub_only: RSAKeyPair | None = None   # public key only

        self._build()

    # ══════════════════════════════════════════════════════════════════════════
    #  TOP-LEVEL LAYOUT
    # ══════════════════════════════════════════════════════════════════════════

    def _build(self):
        self._header()
        tk.Frame(self, bg=CYAN_DK, height=1).pack(fill="x")
        self._notebook()
        self._status_bar()

    # ── Header ────────────────────────────────────────────────────────────────

    def _header(self):
        hdr = tk.Frame(self, bg=PANEL, pady=10, padx=18)
        hdr.pack(fill="x")

        VaultLock(hdr).pack(side="left", padx=(0, 14))

        info = tk.Frame(hdr, bg=PANEL)
        info.pack(side="left")
        tk.Label(info, text="CRYPTOVAULT",
                 font=("Courier New", 20, "bold"), bg=PANEL, fg=CYAN).pack(anchor="w")
        tk.Label(info, text="AES-256-GCM  ·  RSA-2048/4096  ·  Hybrid Encryption  ·  Digital Signatures",
                 font=MF_XS, bg=PANEL, fg=MUTED).pack(anchor="w")

        # Right side: key load status indicators
        right = tk.Frame(hdr, bg=PANEL)
        right.pack(side="right")

        tk.Label(right, text="KEY STATUS", font=MF_XS, bg=PANEL,
                 fg=MUTED).pack(anchor="e", pady=(0, 4))

        self._ind_priv = self._key_led(right, "Private Key")
        self._ind_pub  = self._key_led(right, "Public Key")

        # Clock
        self._clock_var = tk.StringVar()
        tk.Label(hdr, textvariable=self._clock_var, font=MF_XS,
                 bg=PANEL, fg=CYAN_DK).pack(side="right", padx=20)
        self._tick_clock()

    def _key_led(self, parent, label: str):
        row = tk.Frame(parent, bg=PANEL)
        row.pack(anchor="e", pady=1)
        dot = tk.Label(row, text="●", font=("Courier New", 9), bg=PANEL, fg=MUTED)
        dot.pack(side="right", padx=(4, 0))
        tk.Label(row, text=label, font=MF_XS, bg=PANEL, fg=MUTED).pack(side="right")
        return dot

    def _set_key_led(self, dot: tk.Label, loaded: bool):
        dot.config(fg=GREEN if loaded else MUTED)

    def _tick_clock(self):
        self._clock_var.set(datetime.now().strftime("%Y-%m-%d  %H:%M:%S"))
        self.after(1000, self._tick_clock)

    # ── Notebook ──────────────────────────────────────────────────────────────

    def _notebook(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Vault.TNotebook",
                        background=BG, borderwidth=0,
                        tabmargins=[0, 0, 0, 0])
        style.configure("Vault.TNotebook.Tab",
                        background=CARD, foreground=MUTED,
                        font=SF_B, padding=[14, 6],
                        borderwidth=0)
        style.map("Vault.TNotebook.Tab",
                  background=[("selected", PANEL)],
                  foreground=[("selected", CYAN)])

        self.nb = ttk.Notebook(self, style="Vault.TNotebook")
        self.nb.pack(fill="both", expand=True, padx=0, pady=0)

        self._tab_aes()
        self._tab_rsa_keys()
        self._tab_hybrid()
        self._tab_signature()
        self._tab_hash()
        self._tab_file()

    # ── Status bar ────────────────────────────────────────────────────────────

    def _status_bar(self):
        bar = tk.Frame(self, bg="#030810", pady=4)
        bar.pack(fill="x")
        self._status_var = tk.StringVar(value="◈  READY  —  CryptoVault initialised")
        tk.Label(bar, textvariable=self._status_var,
                 font=MF_XS, bg="#030810", fg=MUTED).pack(side="left", padx=14)
        self._prog = ttk.Progressbar(bar, mode="indeterminate", length=160)
        ttk.Style().configure("Vault.Horizontal.TProgressbar",
                              troughcolor=CARD, background=CYAN_DK)
        self._prog.pack(side="right", padx=14, pady=2)

    def _set_status(self, msg: str, color=MUTED):
        self._status_var.set(f"◈  {msg}")

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB 1 — AES-256-GCM  (Password-Based)
    # ══════════════════════════════════════════════════════════════════════════

    def _tab_aes(self):
        frame = tk.Frame(self.nb, bg=CARD)
        self.nb.add(frame, text="  🔐 AES Cipher  ")

        # Split into left (encrypt) and right (decrypt)
        split = tk.Frame(frame, bg=CARD)
        split.pack(fill="both", expand=True, padx=14, pady=10)

        # ── LEFT: Encrypt ──────────────────────────────────────────────────
        lf = tk.LabelFrame(split, text=" ENCRYPT ", font=MF_B,
                           bg=CARD, fg=CYAN_DK,
                           highlightbackground=BORDER, bd=1,
                           labelanchor="nw", padx=12, pady=8)
        lf.pack(side="left", fill="both", expand=True, padx=(0, 6))

        section_label(lf, "Plaintext Input", bg=CARD)
        self._aes_plain_in = text_area(lf, height=7, pady=(0, 0))

        self._aes_pass_enc = tk.StringVar()
        entry_row(lf, "Password", self._aes_pass_enc, show="●", bg=CARD)

        self._aes_pass2 = tk.StringVar()
        entry_row(lf, "Confirm Password", self._aes_pass2, show="●", bg=CARD)

        section_label(lf, "Ciphertext Output (Base64)", bg=CARD)
        self._aes_ct_out = text_area(lf, height=5, bg=PANEL, pady=(0, 0))

        btn_row = tk.Frame(lf, bg=CARD)
        btn_row.pack(fill="x", pady=(8, 0))
        cyan_btn(btn_row, "🔒  ENCRYPT", self._aes_encrypt,
                 bg="#003344").pack(side="left")
        cyan_btn(btn_row, "⎘  Copy", lambda: self._copy(self._aes_ct_out),
                 bg=PANEL, fg=MUTED).pack(side="left", padx=6)
        cyan_btn(btn_row, "✕  Clear", lambda: self._clear_texts(
                 self._aes_plain_in, self._aes_ct_out),
                 bg=PANEL, fg=MUTED).pack(side="left")

        # ── RIGHT: Decrypt ─────────────────────────────────────────────────
        rf = tk.LabelFrame(split, text=" DECRYPT ", font=MF_B,
                           bg=CARD, fg=CYAN_DK,
                           highlightbackground=BORDER, bd=1,
                           labelanchor="nw", padx=12, pady=8)
        rf.pack(side="left", fill="both", expand=True, padx=(6, 0))

        section_label(rf, "Ciphertext Input (Base64)", bg=CARD)
        self._aes_ct_in = text_area(rf, height=7, pady=(0, 0))

        self._aes_pass_dec = tk.StringVar()
        entry_row(rf, "Password", self._aes_pass_dec, show="●", bg=CARD)

        section_label(rf, "Plaintext Output", bg=CARD)
        self._aes_plain_out = text_area(rf, height=5, bg=PANEL, pady=(0, 0))

        btn_row2 = tk.Frame(rf, bg=CARD)
        btn_row2.pack(fill="x", pady=(8, 0))
        cyan_btn(btn_row2, "🔓  DECRYPT", self._aes_decrypt,
                 bg="#003344").pack(side="left")
        cyan_btn(btn_row2, "⎘  Copy", lambda: self._copy(self._aes_plain_out),
                 bg=PANEL, fg=MUTED).pack(side="left", padx=6)

        # Info footer
        info = tk.Frame(frame, bg=PANEL, pady=6, padx=14)
        info.pack(fill="x")
        tk.Label(info,
                 text="Algorithm: AES-256-GCM  ·  KDF: PBKDF2-HMAC-SHA256 (480,000 iterations)  ·  Salt: 256-bit  ·  Nonce: 96-bit",
                 font=MF_XS, bg=PANEL, fg=MUTED).pack(side="left")

    def _aes_encrypt(self):
        pt = self._aes_plain_in.get("1.0", "end-1c").strip()
        pw = self._aes_pass_enc.get()
        pw2 = self._aes_pass2.get()
        if not pt:
            return messagebox.showwarning("Empty", "Enter plaintext to encrypt.")
        if not pw:
            return messagebox.showwarning("No Password", "Enter an encryption password.")
        if pw != pw2:
            return messagebox.showerror("Mismatch", "Passwords do not match.")
        try:
            ct = AESCipher.encrypt_text(pt, pw)
            self._aes_ct_out.config(state="normal")
            self._aes_ct_out.delete("1.0", "end")
            self._aes_ct_out.insert("end", ct)
            self._set_status("AES-256-GCM encryption successful ✔")
        except Exception as ex:
            messagebox.showerror("Error", str(ex))

    def _aes_decrypt(self):
        ct = self._aes_ct_in.get("1.0", "end-1c").strip()
        pw = self._aes_pass_dec.get()
        if not ct:
            return messagebox.showwarning("Empty", "Paste ciphertext to decrypt.")
        if not pw:
            return messagebox.showwarning("No Password", "Enter the decryption password.")
        try:
            pt = AESCipher.decrypt_text(ct, pw)
            self._aes_plain_out.config(state="normal")
            self._aes_plain_out.delete("1.0", "end")
            self._aes_plain_out.insert("end", pt)
            self._set_status("AES-256-GCM decryption successful ✔")
        except Exception as ex:
            messagebox.showerror("Decryption Failed", str(ex))

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB 2 — RSA KEY MANAGER
    # ══════════════════════════════════════════════════════════════════════════

    def _tab_rsa_keys(self):
        frame = tk.Frame(self.nb, bg=CARD)
        self.nb.add(frame, text="  🔑 RSA Keys  ")

        main = tk.Frame(frame, bg=CARD, padx=14, pady=10)
        main.pack(fill="both", expand=True)

        # Controls
        ctrl = tk.LabelFrame(main, text=" KEY GENERATION ", font=MF_B,
                             bg=CARD, fg=CYAN_DK, highlightbackground=BORDER,
                             bd=1, padx=12, pady=8)
        ctrl.pack(fill="x", pady=(0, 10))

        cr = tk.Frame(ctrl, bg=CARD)
        cr.pack(fill="x")

        tk.Label(cr, text="Key Size:", font=MF_B, bg=CARD, fg=TEXT).pack(side="left")
        self._rsa_size_var = tk.StringVar(value="2048")
        for sz in ("2048", "4096"):
            tk.Radiobutton(cr, text=f"RSA-{sz}", variable=self._rsa_size_var,
                           value=sz, bg=CARD, fg=CYAN2, selectcolor=PANEL,
                           activebackground=CARD, activeforeground=CYAN,
                           font=MF_B).pack(side="left", padx=8)

        self._rsa_pw_var = tk.StringVar()
        entry_row(ctrl, "Protect with password (opt.)", self._rsa_pw_var,
                  show="●", bg=CARD)

        btn_r = tk.Frame(ctrl, bg=CARD)
        btn_r.pack(fill="x", pady=(8, 0))
        self._gen_btn = cyan_btn(btn_r, "⚙  GENERATE KEY PAIR", self._rsa_generate,
                                 bg="#002233")
        self._gen_btn.pack(side="left")
        self._rsa_status_lbl = tk.Label(btn_r, text="No key loaded",
                                        font=MF_S, bg=CARD, fg=MUTED)
        self._rsa_status_lbl.pack(side="left", padx=12)

        # Key display (left/right)
        keys_row = tk.Frame(main, bg=CARD)
        keys_row.pack(fill="both", expand=True)

        # Private key
        pf = tk.LabelFrame(keys_row, text=" PRIVATE KEY (keep secret) ",
                           font=MF_B, bg=CARD, fg=RED,
                           highlightbackground=BORDER, bd=1,
                           padx=8, pady=6)
        pf.pack(side="left", fill="both", expand=True, padx=(0, 6))

        self._priv_text = text_area(pf, height=14, bg="#0a0012", fg="#ff8080")
        pb = tk.Frame(pf, bg=CARD)
        pb.pack(fill="x", pady=(4, 0))
        cyan_btn(pb, "💾  Save .pem", self._save_private,
                 bg="#1a0008", fg=RED).pack(side="left")
        cyan_btn(pb, "📂  Load .pem", self._load_private,
                 bg=PANEL, fg=MUTED).pack(side="left", padx=6)
        cyan_btn(pb, "⎘  Copy", lambda: self._copy(self._priv_text),
                 bg=PANEL, fg=MUTED).pack(side="left")

        # Public key
        qf = tk.LabelFrame(keys_row, text=" PUBLIC KEY (shareable) ",
                           font=MF_B, bg=CARD, fg=GREEN,
                           highlightbackground=BORDER, bd=1,
                           padx=8, pady=6)
        qf.pack(side="left", fill="both", expand=True, padx=(6, 0))

        self._pub_text = text_area(qf, height=14, bg="#001a08", fg="#80ff80")
        qb = tk.Frame(qf, bg=CARD)
        qb.pack(fill="x", pady=(4, 0))
        cyan_btn(qb, "💾  Save .pem", self._save_public,
                 bg="#001a08", fg=GREEN).pack(side="left")
        cyan_btn(qb, "📂  Load .pem", self._load_public,
                 bg=PANEL, fg=MUTED).pack(side="left", padx=6)
        cyan_btn(qb, "⎘  Copy", lambda: self._copy(self._pub_text),
                 bg=PANEL, fg=MUTED).pack(side="left")

        # Fingerprint bar
        fp_bar = tk.Frame(main, bg=PANEL, pady=5, padx=12)
        fp_bar.pack(fill="x", pady=(6, 0))
        tk.Label(fp_bar, text="SHA-256 Fingerprint:", font=MF_XS,
                 bg=PANEL, fg=MUTED).pack(side="left")
        self._fp_var = tk.StringVar(value="—")
        tk.Label(fp_bar, textvariable=self._fp_var, font=MF_XS,
                 bg=PANEL, fg=CYAN_DK).pack(side="left", padx=8)

    def _rsa_generate(self):
        size = int(self._rsa_size_var.get())
        pw   = self._rsa_pw_var.get() or None
        self._gen_btn.config(state="disabled")
        self._rsa_status_lbl.config(text="Generating…", fg=ORANGE)
        self._prog.start(10)

        def _gen():
            kp = RSAKeyPair(size)
            kp.generate()
            self._key_pair = kp
            priv_pem = kp.export_private_pem(pw)
            pub_pem  = kp.export_public_pem()
            fp       = kp.export_public_fingerprint()
            self.after(0, self._rsa_gen_done, priv_pem, pub_pem, fp)

        threading.Thread(target=_gen, daemon=True).start()

    def _rsa_gen_done(self, priv_pem, pub_pem, fp):
        self._prog.stop()
        self._gen_btn.config(state="normal")
        self._rsa_status_lbl.config(text="✔ Key pair generated", fg=GREEN)

        self._priv_text.config(state="normal")
        self._priv_text.delete("1.0", "end")
        self._priv_text.insert("end", priv_pem)

        self._pub_text.config(state="normal")
        self._pub_text.delete("1.0", "end")
        self._pub_text.insert("end", pub_pem)

        self._fp_var.set(fp)
        self._set_key_led(self._ind_priv, True)
        self._set_key_led(self._ind_pub,  True)
        self._set_status(f"RSA-{self._rsa_size_var.get()} key pair generated ✔")

    def _save_private(self):
        if not self._key_pair:
            return messagebox.showinfo("No Key", "Generate a key pair first.")
        path = filedialog.asksaveasfilename(defaultextension=".pem",
               filetypes=[("PEM Key", "*.pem"), ("All", "*.*")],
               initialfile="private_key.pem")
        if path:
            pw = self._rsa_pw_var.get() or None
            self._key_pair.save_private(path, pw)
            messagebox.showinfo("Saved", f"Private key saved:\n{path}")

    def _save_public(self):
        if not self._key_pair:
            return messagebox.showinfo("No Key", "Generate a key pair first.")
        path = filedialog.asksaveasfilename(defaultextension=".pem",
               filetypes=[("PEM Key", "*.pem"), ("All", "*.*")],
               initialfile="public_key.pem")
        if path:
            self._key_pair.save_public(path)
            messagebox.showinfo("Saved", f"Public key saved:\n{path}")

    def _load_private(self):
        path = filedialog.askopenfilename(
               filetypes=[("PEM Key", "*.pem"), ("All", "*.*")])
        if not path:
            return
        pw = self._rsa_pw_var.get() or None
        try:
            kp = RSAKeyPair.load_private_pem(Path(path).read_text(), pw)
            self._key_pair = kp
            priv_pem = kp.export_private_pem(pw)
            pub_pem  = kp.export_public_pem()
            fp       = kp.export_public_fingerprint()

            self._priv_text.config(state="normal")
            self._priv_text.delete("1.0","end")
            self._priv_text.insert("end", priv_pem)
            self._pub_text.config(state="normal")
            self._pub_text.delete("1.0","end")
            self._pub_text.insert("end", pub_pem)
            self._fp_var.set(fp)
            self._rsa_status_lbl.config(text=f"✔ Loaded: {Path(path).name}", fg=GREEN)
            self._set_key_led(self._ind_priv, True)
            self._set_key_led(self._ind_pub,  True)
            self._set_status("Private key loaded ✔")
        except Exception as ex:
            messagebox.showerror("Load Error", str(ex))

    def _load_public(self):
        path = filedialog.askopenfilename(
               filetypes=[("PEM Key", "*.pem"), ("All", "*.*")])
        if not path:
            return
        try:
            kp = RSAKeyPair.load_public_pem(Path(path).read_text())
            self._pub_only = kp
            pub_pem = kp.export_public_pem()
            self._pub_text.config(state="normal")
            self._pub_text.delete("1.0","end")
            self._pub_text.insert("end", pub_pem)
            self._set_key_led(self._ind_pub, True)
            self._set_status("Public key loaded ✔")
        except Exception as ex:
            messagebox.showerror("Load Error", str(ex))

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB 3 — HYBRID RSA + AES  (Secure Transmission Envelope)
    # ══════════════════════════════════════════════════════════════════════════

    def _tab_hybrid(self):
        frame = tk.Frame(self.nb, bg=CARD)
        self.nb.add(frame, text="  📨 Hybrid (RSA+AES)  ")

        info = tk.Frame(frame, bg=PANEL, pady=6, padx=14)
        info.pack(fill="x")
        tk.Label(info,
                 text="Encrypts with recipient's public key — only their private key can decrypt.  "
                      "Ephemeral AES-256-GCM session key, RSA-OAEP wrapped.",
                 font=MF_XS, bg=PANEL, fg=MUTED, wraplength=900, justify="left").pack(anchor="w")

        split = tk.Frame(frame, bg=CARD)
        split.pack(fill="both", expand=True, padx=14, pady=10)

        # ENCRYPT side
        ef = tk.LabelFrame(split, text=" ENCRYPT (needs recipient public key) ",
                           font=MF_B, bg=CARD, fg=CYAN_DK,
                           highlightbackground=BORDER, bd=1, padx=12, pady=8)
        ef.pack(side="left", fill="both", expand=True, padx=(0, 6))

        section_label(ef, "Plaintext (any size)", bg=CARD)
        self._hyb_plain_in = text_area(ef, height=8)

        section_label(ef, "Recipient Public Key (.pem) — or use loaded key", bg=CARD)
        self._hyb_pub_in = text_area(ef, height=5, bg=PANEL, fg="#80ff80")
        tk.Label(ef, text="Leave empty to use the key loaded in the RSA Key Manager tab.",
                 font=MF_XS, bg=CARD, fg=MUTED).pack(anchor="w")

        section_label(ef, "Encrypted Output (Base64)", bg=CARD)
        self._hyb_ct_out = text_area(ef, height=5)

        eb = tk.Frame(ef, bg=CARD)
        eb.pack(fill="x", pady=(6, 0))
        cyan_btn(eb, "🔒  ENCRYPT", self._hybrid_encrypt, bg="#003344").pack(side="left")
        cyan_btn(eb, "⎘  Copy", lambda: self._copy(self._hyb_ct_out),
                 bg=PANEL, fg=MUTED).pack(side="left", padx=6)

        # DECRYPT side
        df = tk.LabelFrame(split, text=" DECRYPT (needs your private key) ",
                           font=MF_B, bg=CARD, fg=CYAN_DK,
                           highlightbackground=BORDER, bd=1, padx=12, pady=8)
        df.pack(side="left", fill="both", expand=True, padx=(6, 0))

        section_label(df, "Ciphertext Input (Base64)", bg=CARD)
        self._hyb_ct_in = text_area(df, height=8)

        tk.Label(df,
                 text="Uses the private key loaded in the RSA Key Manager tab.",
                 font=MF_XS, bg=CARD, fg=MUTED).pack(anchor="w", pady=(4, 0))

        section_label(df, "Decrypted Plaintext", bg=CARD)
        self._hyb_plain_out = text_area(df, height=9, bg=PANEL)

        db = tk.Frame(df, bg=CARD)
        db.pack(fill="x", pady=(6, 0))
        cyan_btn(db, "🔓  DECRYPT", self._hybrid_decrypt, bg="#003344").pack(side="left")
        cyan_btn(db, "⎘  Copy", lambda: self._copy(self._hyb_plain_out),
                 bg=PANEL, fg=MUTED).pack(side="left", padx=6)

    def _get_public_key(self):
        """Return the best available public key."""
        pem = self._hyb_pub_in.get("1.0", "end-1c").strip()
        if pem:
            return RSAKeyPair.load_public_pem(pem).public_key
        if self._key_pair:
            return self._key_pair.public_key
        if self._pub_only:
            return self._pub_only.public_key
        return None

    def _hybrid_encrypt(self):
        pt  = self._hyb_plain_in.get("1.0", "end-1c").strip()
        pub = self._get_public_key()
        if not pt:
            return messagebox.showwarning("Empty", "Enter plaintext.")
        if not pub:
            return messagebox.showwarning("No Key",
                   "Paste a public key or load one in the RSA Key Manager tab.")
        try:
            ct = HybridCipher.encrypt_text(pt, pub)
            self._hyb_ct_out.config(state="normal")
            self._hyb_ct_out.delete("1.0", "end")
            self._hyb_ct_out.insert("end", ct)
            self._set_status("Hybrid encryption successful ✔")
        except Exception as ex:
            messagebox.showerror("Error", str(ex))

    def _hybrid_decrypt(self):
        ct = self._hyb_ct_in.get("1.0", "end-1c").strip()
        if not ct:
            return messagebox.showwarning("Empty", "Paste ciphertext.")
        if not self._key_pair:
            return messagebox.showwarning("No Private Key",
                   "Load or generate a key pair in the RSA Key Manager tab first.")
        try:
            pt = HybridCipher.decrypt_text(ct, self._key_pair.private_key)
            self._hyb_plain_out.config(state="normal")
            self._hyb_plain_out.delete("1.0", "end")
            self._hyb_plain_out.insert("end", pt)
            self._set_status("Hybrid decryption successful ✔")
        except Exception as ex:
            messagebox.showerror("Decryption Failed", str(ex))

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB 4 — DIGITAL SIGNATURES
    # ══════════════════════════════════════════════════════════════════════════

    def _tab_signature(self):
        frame = tk.Frame(self.nb, bg=CARD)
        self.nb.add(frame, text="  ✍ Signatures  ")

        split = tk.Frame(frame, bg=CARD)
        split.pack(fill="both", expand=True, padx=14, pady=10)

        # SIGN
        sf = tk.LabelFrame(split, text=" SIGN (needs private key) ",
                           font=MF_B, bg=CARD, fg=CYAN_DK,
                           highlightbackground=BORDER, bd=1, padx=12, pady=8)
        sf.pack(side="left", fill="both", expand=True, padx=(0, 6))

        section_label(sf, "Message to Sign", bg=CARD)
        self._sig_msg_in = text_area(sf, height=8)

        section_label(sf, "RSA-PSS Signature (Base64)", bg=CARD)
        self._sig_out = text_area(sf, height=5, bg=PANEL)

        sb2 = tk.Frame(sf, bg=CARD)
        sb2.pack(fill="x", pady=(6, 0))
        cyan_btn(sb2, "✍  SIGN MESSAGE", self._sign_msg, bg="#003344").pack(side="left")
        cyan_btn(sb2, "⎘  Copy Sig", lambda: self._copy(self._sig_out),
                 bg=PANEL, fg=MUTED).pack(side="left", padx=6)

        # VERIFY
        vf = tk.LabelFrame(split, text=" VERIFY (needs public key) ",
                           font=MF_B, bg=CARD, fg=CYAN_DK,
                           highlightbackground=BORDER, bd=1, padx=12, pady=8)
        vf.pack(side="left", fill="both", expand=True, padx=(6, 0))

        section_label(vf, "Original Message", bg=CARD)
        self._ver_msg = text_area(vf, height=6)

        section_label(vf, "Signature to Verify (Base64)", bg=CARD)
        self._ver_sig = text_area(vf, height=5)

        section_label(vf, "Verification Result", bg=CARD)
        self._ver_result = text_area(vf, height=3, bg=PANEL)

        vb = tk.Frame(vf, bg=CARD)
        vb.pack(fill="x", pady=(6, 0))
        cyan_btn(vb, "✔  VERIFY SIGNATURE", self._verify_sig,
                 bg="#003344").pack(side="left")

        info = tk.Frame(frame, bg=PANEL, pady=6, padx=14)
        info.pack(fill="x")
        tk.Label(info,
                 text="Algorithm: RSA-PSS  ·  Hash: SHA-256  ·  "
                      "Uses keys from the RSA Key Manager tab",
                 font=MF_XS, bg=PANEL, fg=MUTED).pack(side="left")

    def _sign_msg(self):
        msg = self._sig_msg_in.get("1.0", "end-1c").strip()
        if not msg:
            return messagebox.showwarning("Empty", "Enter a message to sign.")
        if not self._key_pair:
            return messagebox.showwarning("No Private Key",
                   "Load or generate a key pair in the RSA Key Manager tab.")
        try:
            sig = DigitalSigner.sign_text(msg, self._key_pair.private_key)
            self._sig_out.config(state="normal")
            self._sig_out.delete("1.0", "end")
            self._sig_out.insert("end", sig)
            self._set_status("Message signed with RSA-PSS/SHA-256 ✔")
        except Exception as ex:
            messagebox.showerror("Signing Error", str(ex))

    def _verify_sig(self):
        msg = self._ver_msg.get("1.0", "end-1c").strip()
        sig = self._ver_sig.get("1.0", "end-1c").strip()
        if not msg or not sig:
            return messagebox.showwarning("Empty", "Enter message and signature.")
        pub = self._get_public_key()
        if not pub:
            return messagebox.showwarning("No Public Key",
                   "Load a public key in the RSA Key Manager tab.")
        try:
            valid = DigitalSigner.verify_text(msg, sig, pub)
            result = "✔  SIGNATURE VALID — message is authentic" if valid \
                     else "✘  SIGNATURE INVALID — message may be tampered"
            self._ver_result.config(state="normal")
            self._ver_result.delete("1.0", "end")
            self._ver_result.insert("end", result,
                                    "valid" if valid else "invalid")
            self._ver_result.tag_configure("valid",   foreground=GREEN)
            self._ver_result.tag_configure("invalid", foreground=RED)
            self._set_status(f"Signature verification: {'VALID ✔' if valid else 'INVALID ✘'}")
        except Exception as ex:
            messagebox.showerror("Verification Error", str(ex))

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB 5 — HASH UTILITY
    # ══════════════════════════════════════════════════════════════════════════

    def _tab_hash(self):
        frame = tk.Frame(self.nb, bg=CARD)
        self.nb.add(frame, text="  #  Hash Utility  ")

        main = tk.Frame(frame, bg=CARD, padx=14, pady=10)
        main.pack(fill="both", expand=True)

        # Algorithm selector
        alg_row = tk.Frame(main, bg=CARD)
        alg_row.pack(fill="x", pady=(0, 8))
        tk.Label(alg_row, text="Algorithm:", font=MF_B, bg=CARD, fg=TEXT).pack(side="left")
        self._hash_alg = tk.StringVar(value="SHA-256")
        for alg in Hasher.ALGORITHMS:
            tk.Radiobutton(alg_row, text=alg, variable=self._hash_alg, value=alg,
                           bg=CARD, fg=CYAN2, selectcolor=PANEL,
                           activebackground=CARD, font=MF_S).pack(side="left", padx=6)

        split = tk.Frame(main, bg=CARD)
        split.pack(fill="both", expand=True)

        # TEXT hashing
        tf = tk.LabelFrame(split, text=" HASH TEXT ", font=MF_B,
                           bg=CARD, fg=CYAN_DK,
                           highlightbackground=BORDER, bd=1, padx=12, pady=8)
        tf.pack(side="left", fill="both", expand=True, padx=(0, 6))

        section_label(tf, "Input Text", bg=CARD)
        self._hash_txt_in = text_area(tf, height=8)

        section_label(tf, "Digest (Hex)", bg=CARD)
        self._hash_txt_out = text_area(tf, height=3, bg=PANEL)

        tb = tk.Frame(tf, bg=CARD)
        tb.pack(fill="x", pady=(6, 0))
        cyan_btn(tb, "#  HASH TEXT", self._hash_text, bg="#003344").pack(side="left")
        cyan_btn(tb, "⎘  Copy", lambda: self._copy(self._hash_txt_out),
                 bg=PANEL, fg=MUTED).pack(side="left", padx=6)

        # FILE hashing
        ff = tk.LabelFrame(split, text=" HASH FILE ", font=MF_B,
                           bg=CARD, fg=CYAN_DK,
                           highlightbackground=BORDER, bd=1, padx=12, pady=8)
        ff.pack(side="left", fill="both", expand=True, padx=(6, 0))

        self._hash_file_var = tk.StringVar()
        entry_row(ff, "File Path", self._hash_file_var, bg=CARD)

        fb2 = tk.Frame(ff, bg=CARD)
        fb2.pack(fill="x", pady=4)
        cyan_btn(fb2, "📂  Browse", self._browse_hash_file,
                 bg=PANEL, fg=MUTED).pack(side="left")

        section_label(ff, "File Hash Output", bg=CARD)
        self._hash_file_out = text_area(ff, height=8, bg=PANEL)

        fb3 = tk.Frame(ff, bg=CARD)
        fb3.pack(fill="x", pady=(6, 0))
        cyan_btn(fb3, "#  HASH FILE", self._hash_file, bg="#003344").pack(side="left")
        cyan_btn(fb3, "⎘  Copy", lambda: self._copy(self._hash_file_out),
                 bg=PANEL, fg=MUTED).pack(side="left", padx=6)

    def _hash_text(self):
        txt = self._hash_txt_in.get("1.0", "end-1c")
        alg = self._hash_alg.get()
        try:
            digest = Hasher.hash_text(txt, alg)
            self._hash_txt_out.config(state="normal")
            self._hash_txt_out.delete("1.0", "end")
            self._hash_txt_out.insert("end", f"{alg}: {digest}")
            self._set_status(f"{alg} hash computed ✔")
        except Exception as ex:
            messagebox.showerror("Error", str(ex))

    def _browse_hash_file(self):
        path = filedialog.askopenfilename()
        if path:
            self._hash_file_var.set(path)

    def _hash_file(self):
        path = self._hash_file_var.get().strip()
        alg  = self._hash_alg.get()
        if not path:
            return messagebox.showwarning("No File", "Select a file.")
        try:
            result = Hasher.hash_file(path, alg)
            out = (f"File      : {result['file']}\n"
                   f"Size      : {result['size']}\n"
                   f"Algorithm : {result['algorithm']}\n"
                   f"Digest    : {result['digest']}")
            self._hash_file_out.config(state="normal")
            self._hash_file_out.delete("1.0", "end")
            self._hash_file_out.insert("end", out)
            self._set_status(f"File hashed with {alg} ✔")
        except Exception as ex:
            messagebox.showerror("Error", str(ex))

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB 6 — FILE ENCRYPTION
    # ══════════════════════════════════════════════════════════════════════════

    def _tab_file(self):
        frame = tk.Frame(self.nb, bg=CARD)
        self.nb.add(frame, text="  📁 File Crypto  ")

        main = tk.Frame(frame, bg=CARD, padx=14, pady=10)
        main.pack(fill="both", expand=True)

        # Mode toggle
        mode_row = tk.Frame(main, bg=CARD)
        mode_row.pack(fill="x", pady=(0, 10))
        tk.Label(mode_row, text="Mode:", font=MF_B, bg=CARD, fg=TEXT).pack(side="left")
        self._file_mode = tk.StringVar(value="AES")
        for mode, label in [("AES", "AES-256-GCM (password)"),
                             ("HYBRID", "Hybrid RSA+AES (key pair)")]:
            tk.Radiobutton(mode_row, text=label, variable=self._file_mode, value=mode,
                           bg=CARD, fg=CYAN2, selectcolor=PANEL,
                           activebackground=CARD, font=MF_B).pack(side="left", padx=10)

        split = tk.Frame(main, bg=CARD)
        split.pack(fill="both", expand=True)

        # ENCRYPT FILE side
        ef = tk.LabelFrame(split, text=" ENCRYPT FILE ", font=MF_B,
                           bg=CARD, fg=CYAN_DK,
                           highlightbackground=BORDER, bd=1, padx=12, pady=8)
        ef.pack(side="left", fill="both", expand=True, padx=(0, 6))

        self._fenc_src = tk.StringVar()
        self._fenc_dst = tk.StringVar()
        self._fenc_pw  = tk.StringVar()

        entry_row(ef, "Input File", self._fenc_src, bg=CARD)
        br1 = tk.Frame(ef, bg=CARD)
        br1.pack(fill="x", pady=2)
        cyan_btn(br1, "📂  Browse", lambda: self._browse_set(self._fenc_src),
                 bg=PANEL, fg=MUTED).pack(side="left")

        entry_row(ef, "Output File (.enc)", self._fenc_dst, bg=CARD)
        br2 = tk.Frame(ef, bg=CARD)
        br2.pack(fill="x", pady=2)
        cyan_btn(br2, "📂  Browse", lambda: self._browse_save(self._fenc_dst, ".enc"),
                 bg=PANEL, fg=MUTED).pack(side="left")

        entry_row(ef, "Password (AES mode)", self._fenc_pw, show="●", bg=CARD)
        tk.Label(ef, text="(Leave blank when using Hybrid RSA+AES mode)",
                 font=MF_XS, bg=CARD, fg=MUTED).pack(anchor="w")

        section_label(ef, "Encryption Result", bg=CARD)
        self._fenc_result = text_area(ef, height=6, bg=PANEL)

        eb = tk.Frame(ef, bg=CARD)
        eb.pack(fill="x", pady=(6, 0))
        cyan_btn(eb, "🔒  ENCRYPT FILE", self._encrypt_file,
                 bg="#003344").pack(side="left")

        # DECRYPT FILE side
        df = tk.LabelFrame(split, text=" DECRYPT FILE ", font=MF_B,
                           bg=CARD, fg=CYAN_DK,
                           highlightbackground=BORDER, bd=1, padx=12, pady=8)
        df.pack(side="left", fill="both", expand=True, padx=(6, 0))

        self._fdec_src = tk.StringVar()
        self._fdec_dst = tk.StringVar()
        self._fdec_pw  = tk.StringVar()

        entry_row(df, "Encrypted File (.enc)", self._fdec_src, bg=CARD)
        dr1 = tk.Frame(df, bg=CARD)
        dr1.pack(fill="x", pady=2)
        cyan_btn(dr1, "📂  Browse", lambda: self._browse_set(self._fdec_src),
                 bg=PANEL, fg=MUTED).pack(side="left")

        entry_row(df, "Output File", self._fdec_dst, bg=CARD)
        dr2 = tk.Frame(df, bg=CARD)
        dr2.pack(fill="x", pady=2)
        cyan_btn(dr2, "📂  Browse", lambda: self._browse_save(self._fdec_dst, ""),
                 bg=PANEL, fg=MUTED).pack(side="left")

        entry_row(df, "Password (AES mode)", self._fdec_pw, show="●", bg=CARD)
        tk.Label(df, text="(Leave blank when using Hybrid RSA+AES mode)",
                 font=MF_XS, bg=CARD, fg=MUTED).pack(anchor="w")

        section_label(df, "Decryption Result", bg=CARD)
        self._fdec_result = text_area(df, height=6, bg=PANEL)

        db = tk.Frame(df, bg=CARD)
        db.pack(fill="x", pady=(6, 0))
        cyan_btn(db, "🔓  DECRYPT FILE", self._decrypt_file,
                 bg="#003344").pack(side="left")

    def _encrypt_file(self):
        src  = self._fenc_src.get().strip()
        dst  = self._fenc_dst.get().strip()
        pw   = self._fenc_pw.get()
        mode = self._file_mode.get()

        if not src or not dst:
            return messagebox.showwarning("Missing", "Select input and output files.")

        def _run():
            try:
                if mode == "AES":
                    if not pw:
                        self.after(0, messagebox.showwarning, "No Password",
                                   "Enter a password for AES mode.")
                        return
                    result = AESCipher.encrypt_file(src, dst, pw)
                else:
                    pub = self._get_public_key()
                    if not pub:
                        self.after(0, messagebox.showwarning, "No Key",
                                   "Load a public key in RSA Key Manager first.")
                        return
                    result = HybridCipher.encrypt_file(src, dst, pub)

                out = "\n".join(f"{k:<18}: {v}" for k, v in result.items())
                def _done():
                    self._fenc_result.config(state="normal")
                    self._fenc_result.delete("1.0","end")
                    self._fenc_result.insert("end", out)
                    self._prog.stop()
                    self._set_status("File encrypted successfully ✔")
                self.after(0, _done)
            except Exception as ex:
                self.after(0, messagebox.showerror, "Error", str(ex))
                self.after(0, self._prog.stop)

        self._prog.start(10)
        self._set_status("Encrypting file…")
        threading.Thread(target=_run, daemon=True).start()

    def _decrypt_file(self):
        src  = self._fdec_src.get().strip()
        dst  = self._fdec_dst.get().strip()
        pw   = self._fdec_pw.get()
        mode = self._file_mode.get()

        if not src or not dst:
            return messagebox.showwarning("Missing", "Select input and output files.")

        def _run():
            try:
                if mode == "AES":
                    if not pw:
                        self.after(0, messagebox.showwarning, "No Password",
                                   "Enter the decryption password.")
                        return
                    result = AESCipher.decrypt_file(src, dst, pw)
                else:
                    if not self._key_pair:
                        self.after(0, messagebox.showwarning, "No Private Key",
                                   "Load a key pair in RSA Key Manager first.")
                        return
                    result = HybridCipher.decrypt_file(src, dst,
                                                       self._key_pair.private_key)

                out = "\n".join(f"{k:<18}: {v}" for k, v in result.items())
                def _done():
                    self._fdec_result.config(state="normal")
                    self._fdec_result.delete("1.0","end")
                    self._fdec_result.insert("end", out)
                    self._prog.stop()
                    self._set_status("File decrypted successfully ✔")
                self.after(0, _done)
            except Exception as ex:
                self.after(0, messagebox.showerror, "Error", str(ex))
                self.after(0, self._prog.stop)

        self._prog.start(10)
        self._set_status("Decrypting file…")
        threading.Thread(target=_run, daemon=True).start()

    # ══════════════════════════════════════════════════════════════════════════
    #  SHARED UTILITIES
    # ══════════════════════════════════════════════════════════════════════════

    def _copy(self, text_widget: tk.Text):
        content = text_widget.get("1.0", "end-1c")
        self.clipboard_clear()
        self.clipboard_append(content)
        self._set_status("Copied to clipboard ✔")

    def _clear_texts(self, *widgets):
        for w in widgets:
            w.config(state="normal")
            w.delete("1.0", "end")

    def _browse_set(self, var: tk.StringVar):
        path = filedialog.askopenfilename()
        if path:
            var.set(path)

    def _browse_save(self, var: tk.StringVar, ext: str):
        path = filedialog.asksaveasfilename(defaultextension=ext)
        if path:
            var.set(path)


# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = EncryptionApp()
    app.mainloop()
