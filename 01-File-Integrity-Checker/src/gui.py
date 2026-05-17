import hashlib
import os
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
import threading

# ── Constants ─────────────────────────────────────────────────────────────────
BASELINE_FILE = os.path.join(os.path.dirname(__file__), "baseline.json")

BG       = "#0d1117"
PANEL    = "#161b22"
BORDER   = "#30363d"
ACCENT   = "#00d4aa"
ACCENT2  = "#58a6ff"
RED      = "#ff4d4d"
YELLOW   = "#e3b341"
GREEN    = "#3fb950"
TEXT     = "#e6edf3"
MUTED    = "#8b949e"
FONT     = ("Consolas", 10)
FONT_B   = ("Consolas", 10, "bold")
FONT_H   = ("Consolas", 13, "bold")
FONT_T   = ("Consolas", 18, "bold")

# ── Core logic ────────────────────────────────────────────────────────────────

def sha256(path: str) -> str | None:
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None

def load_baseline() -> dict:
    if os.path.exists(BASELINE_FILE):
        with open(BASELINE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_baseline(data: dict):
    with open(BASELINE_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ── Widgets ───────────────────────────────────────────────────────────────────

def styled_btn(parent, text, command, color=ACCENT, fg=BG, **kw):
    btn = tk.Button(parent, text=text, command=command,
                    bg=color, fg=fg, activebackground=color,
                    activeforeground=fg, font=FONT_B, relief="flat",
                    padx=12, pady=6, cursor="hand2", bd=0, **kw)
    btn.bind("<Enter>", lambda e: btn.config(bg=_lighten(color)))
    btn.bind("<Leave>", lambda e: btn.config(bg=color))
    return btn

def _lighten(hex_color: str) -> str:
    r, g, b = int(hex_color[1:3],16), int(hex_color[3:5],16), int(hex_color[5:7],16)
    r, g, b = min(255, r+30), min(255, g+30), min(255, b+30)
    return f"#{r:02x}{g:02x}{b:02x}"

# ── Main App ──────────────────────────────────────────────────────────────────

class FileIntegrityApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("File Integrity Checker")
        self.geometry("920x680")
        self.minsize(800, 580)
        self.configure(bg=BG)
        self.baseline = load_baseline()
        self._build_ui()
        self._refresh_table()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=PANEL, pady=14)
        hdr.pack(fill="x")
        tk.Label(hdr, text="🛡  FILE INTEGRITY CHECKER", font=FONT_T,
                 bg=PANEL, fg=ACCENT).pack(side="left", padx=22)
        tk.Label(hdr, text="SHA-256 Tamper Detection", font=("Consolas", 10),
                 bg=PANEL, fg=MUTED).pack(side="left", padx=4)

        # Divider
        tk.Frame(self, bg=ACCENT, height=2).pack(fill="x")

        # Body
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=18, pady=14)

        self._build_left(body)
        self._build_right(body)

    def _build_left(self, parent):
        left = tk.Frame(parent, bg=BG, width=300)
        left.pack(side="left", fill="y", padx=(0, 12))
        left.pack_propagate(False)

        # ── Add file card ──
        card = tk.Frame(left, bg=PANEL, bd=0, pady=14, padx=14)
        card.pack(fill="x", pady=(0, 12))

        tk.Label(card, text="ADD FILES TO MONITOR", font=FONT_B,
                 bg=PANEL, fg=ACCENT2).pack(anchor="w", pady=(0, 8))

        self.path_var = tk.StringVar()
        entry_row = tk.Frame(card, bg=PANEL)
        entry_row.pack(fill="x", pady=(0, 8))

        entry = tk.Entry(entry_row, textvariable=self.path_var, bg="#21262d",
                         fg=TEXT, insertbackground=ACCENT, font=FONT,
                         relief="flat", bd=6)
        entry.pack(side="left", fill="x", expand=True)

        styled_btn(entry_row, "Browse", self._browse,
                   color=ACCENT2).pack(side="left", padx=(6, 0))

        styled_btn(card, "➕  Add & Baseline", self._add_file,
                   color=ACCENT).pack(fill="x")

        # ── Actions card ──
        card2 = tk.Frame(left, bg=PANEL, bd=0, pady=14, padx=14)
        card2.pack(fill="x", pady=(0, 12))

        tk.Label(card2, text="ACTIONS", font=FONT_B,
                 bg=PANEL, fg=ACCENT2).pack(anchor="w", pady=(0, 8))

        styled_btn(card2, "🔍  Verify All Files", self._verify_all,
                   color="#1f6feb").pack(fill="x", pady=(0, 6))
        styled_btn(card2, "🔄  Re-Baseline Selected", self._rebaseline,
                   color=YELLOW, fg="#000").pack(fill="x", pady=(0, 6))
        styled_btn(card2, "🗑  Remove Selected", self._remove_file,
                   color=RED).pack(fill="x")

        # ── Stats card ──
        card3 = tk.Frame(left, bg=PANEL, bd=0, pady=14, padx=14)
        card3.pack(fill="x")

        tk.Label(card3, text="STATISTICS", font=FONT_B,
                 bg=PANEL, fg=ACCENT2).pack(anchor="w", pady=(0, 8))

        self.stat_total  = self._stat_row(card3, "Monitored Files")
        self.stat_ok     = self._stat_row(card3, "Verified OK")
        self.stat_tamper = self._stat_row(card3, "Tampered")
        self.stat_miss   = self._stat_row(card3, "Missing")
        self._update_stats(0, 0, 0, 0)

    def _stat_row(self, parent, label):
        row = tk.Frame(parent, bg=PANEL)
        row.pack(fill="x", pady=2)
        tk.Label(row, text=label, font=FONT, bg=PANEL, fg=MUTED, width=16,
                 anchor="w").pack(side="left")
        val = tk.Label(row, text="—", font=FONT_B, bg=PANEL, fg=TEXT)
        val.pack(side="right")
        return val

    def _update_stats(self, total, ok, tamper, miss):
        self.stat_total.config( text=str(total))
        self.stat_ok.config(    text=str(ok),     fg=GREEN  if ok     else TEXT)
        self.stat_tamper.config(text=str(tamper), fg=RED    if tamper else TEXT)
        self.stat_miss.config(  text=str(miss),   fg=YELLOW if miss   else TEXT)

    def _build_right(self, parent):
        right = tk.Frame(parent, bg=BG)
        right.pack(side="left", fill="both", expand=True)

        tk.Label(right, text="MONITORED FILES", font=FONT_B,
                 bg=BG, fg=ACCENT2).pack(anchor="w", pady=(0, 6))

        # Table
        cols = ("File", "Status", "Hash (SHA-256)", "Last Checked")
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Dark.Treeview",
                         background=PANEL, foreground=TEXT,
                         fieldbackground=PANEL, rowheight=28,
                         font=FONT, borderwidth=0)
        style.configure("Dark.Treeview.Heading",
                         background="#21262d", foreground=ACCENT2,
                         font=FONT_B, relief="flat")
        style.map("Dark.Treeview",
                  background=[("selected", "#1f3a5f")],
                  foreground=[("selected", TEXT)])

        frame = tk.Frame(right, bg=BORDER, bd=1)
        frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(frame, columns=cols, show="headings",
                                  style="Dark.Treeview",
                                  selectmode="browse")
        self.tree.heading("File",         text="File Path")
        self.tree.heading("Status",       text="Status")
        self.tree.heading("Hash (SHA-256)", text="SHA-256 Hash")
        self.tree.heading("Last Checked", text="Last Checked")
        self.tree.column("File",          width=240, anchor="w")
        self.tree.column("Status",        width=120, anchor="center")
        self.tree.column("Hash (SHA-256)", width=200, anchor="w")
        self.tree.column("Last Checked",  width=140, anchor="center")

        sb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        self.tree.tag_configure("ok",      foreground=GREEN)
        self.tree.tag_configure("tamper",  foreground=RED)
        self.tree.tag_configure("missing", foreground=YELLOW)
        self.tree.tag_configure("pending", foreground=MUTED)

        # Log
        tk.Label(right, text="ACTIVITY LOG", font=FONT_B,
                 bg=BG, fg=ACCENT2).pack(anchor="w", pady=(12, 4))

        log_frame = tk.Frame(right, bg=PANEL)
        log_frame.pack(fill="x")

        self.log = tk.Text(log_frame, height=6, bg=PANEL, fg=TEXT,
                           font=("Consolas", 9), relief="flat",
                           state="disabled", insertbackground=ACCENT,
                           wrap="word", padx=8, pady=6)
        log_sb = ttk.Scrollbar(log_frame, orient="vertical", command=self.log.yview)
        self.log.configure(yscrollcommand=log_sb.set)
        self.log.pack(side="left", fill="x", expand=True)
        log_sb.pack(side="right", fill="y")

        self.log.tag_configure("ok",     foreground=GREEN)
        self.log.tag_configure("warn",   foreground=RED)
        self.log.tag_configure("info",   foreground=ACCENT2)
        self.log.tag_configure("yellow", foreground=YELLOW)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _log(self, msg: str, tag="info"):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log.config(state="normal")
        self.log.insert("end", f"[{ts}] {msg}\n", tag)
        self.log.see("end")
        self.log.config(state="disabled")

    def _browse(self):
        path = filedialog.askopenfilename(title="Select a file to monitor")
        if path:
            self.path_var.set(path)

    def _refresh_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for path, info in self.baseline.items():
            name = os.path.basename(path)
            h    = info.get("hash", "")
            ts   = info.get("last_checked", "Never")
            st   = info.get("status", "Pending")
            tag  = {"Verified ✔": "ok", "TAMPERED ✘": "tamper",
                    "Missing ⚠": "missing"}.get(st, "pending")
            self.tree.insert("", "end", iid=path,
                             values=(name, st, h[:20]+"…" if len(h)>22 else h, ts),
                             tags=(tag,))

    def _add_file(self):
        path = self.path_var.get().strip()
        if not path:
            messagebox.showwarning("No File", "Please select or type a file path.")
            return
        if not os.path.exists(path):
            messagebox.showerror("Not Found", f"File not found:\n{path}")
            return
        h = sha256(path)
        self.baseline[path] = {
            "hash": h,
            "status": "Pending",
            "last_checked": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        save_baseline(self.baseline)
        self._refresh_table()
        self._log(f"Baseline created for: {os.path.basename(path)}", "ok")
        self.path_var.set("")

    def _verify_all(self):
        if not self.baseline:
            messagebox.showinfo("Empty", "No files are being monitored yet.")
            return
        self._log("Starting verification of all files…", "info")
        threading.Thread(target=self._run_verify, daemon=True).start()

    def _run_verify(self):
        ok = tamper = miss = 0
        for path, info in self.baseline.items():
            name = os.path.basename(path)
            if not os.path.exists(path):
                info["status"] = "Missing ⚠"
                miss += 1
                self.after(0, self._log, f"MISSING: {name}", "yellow")
            else:
                cur = sha256(path)
                info["last_checked"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                if cur == info["hash"]:
                    info["status"] = "Verified ✔"
                    ok += 1
                    self.after(0, self._log, f"OK: {name}", "ok")
                else:
                    info["status"] = "TAMPERED ✘"
                    tamper += 1
                    self.after(0, self._log, f"TAMPERED: {name}", "warn")
        save_baseline(self.baseline)
        self.after(0, self._refresh_table)
        total = len(self.baseline)
        self.after(0, self._update_stats, total, ok, tamper, miss)
        self.after(0, self._log,
                   f"Done — {ok} OK, {tamper} tampered, {miss} missing", "info")

    def _rebaseline(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Select a file from the table first.")
            return
        path = sel[0]
        if not os.path.exists(path):
            messagebox.showerror("Missing", "File not found on disk.")
            return
        h = sha256(path)
        self.baseline[path]["hash"] = h
        self.baseline[path]["status"] = "Pending"
        self.baseline[path]["last_checked"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        save_baseline(self.baseline)
        self._refresh_table()
        self._log(f"Re-baselined: {os.path.basename(path)}", "ok")

    def _remove_file(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Select a file from the table first.")
            return
        path = sel[0]
        if messagebox.askyesno("Remove", f"Stop monitoring:\n{path}?"):
            del self.baseline[path]
            save_baseline(self.baseline)
            self._refresh_table()
            self._log(f"Removed: {os.path.basename(path)}", "info")


if __name__ == "__main__":
    app = FileIntegrityApp()
    app.mainloop()
