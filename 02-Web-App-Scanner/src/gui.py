"""
Web App Vulnerability Scanner — GUI (Purple Neon / Terminal Theme)
Layout: Top command bar → Phase cards → Split: findings table | terminal log
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
from datetime import datetime
from scanner import WebScanner

# ── Neon Purple Theme (distinct from Project 1's teal/navy) ──────────────────
BG      = "#0f0a1e"   # deep purple-black
PANEL   = "#1a1035"   # dark violet panel
CARD    = "#221545"   # slightly lighter card
BORDER  = "#3d2b6b"   # purple border
ACC     = "#c084fc"   # neon purple accent
ACC2    = "#a78bfa"   # violet
RED     = "#f43f5e"   # rose red
YELLOW  = "#fbbf24"   # amber
GREEN   = "#34d399"   # emerald
CYAN    = "#22d3ee"   # cyan highlight
TEXT    = "#f1f0ff"   # near-white with purple tint
MUTED   = "#7c6fa0"   # muted purple

MF   = ("Courier New", 10)
MF_B = ("Courier New", 10, "bold")
MF_T = ("Courier New", 16, "bold")
MF_S = ("Courier New",  9)

SEVERITY = {
    "SQL Injection":          ("CRITICAL", RED),
    "SQL Injection (Form)":   ("CRITICAL", RED),
    "Reflected XSS":          ("HIGH",     YELLOW),
    "Reflected XSS (Form)":   ("HIGH",     YELLOW),
    "Missing Header":         ("MEDIUM",   ACC),
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def _dk(c):
    r,g,b = int(c[1:3],16),int(c[3:5],16),int(c[5:7],16)
    return f"#{max(0,r-25):02x}{max(0,g-25):02x}{max(0,b-25):02x}"

def _lt(c):
    r,g,b = int(c[1:3],16),int(c[3:5],16),int(c[5:7],16)
    return f"#{min(255,r+30):02x}{min(255,g+30):02x}{min(255,b+30):02x}"

def pill_btn(parent, text, cmd, bg=ACC, fg=BG, **kw):
    b = tk.Button(parent, text=text, command=cmd, bg=bg, fg=fg,
                  activebackground=_lt(bg), activeforeground=fg,
                  font=MF_B, relief="flat", padx=14, pady=7,
                  cursor="hand2", bd=0, **kw)
    b.bind("<Enter>", lambda e: b.config(bg=_lt(bg)))
    b.bind("<Leave>", lambda e: b.config(bg=bg))
    return b


# ── Phase Card widget ─────────────────────────────────────────────────────────

class PhaseCard(tk.Frame):
    """Lights up as a scan phase runs / completes."""
    STATES = {
        "idle":    (CARD,  MUTED,  MUTED,  "○"),
        "active":  (CARD,  ACC,    ACC,    "◉"),
        "done":    (CARD,  GREEN,  GREEN,  "✔"),
        "warn":    (CARD,  YELLOW, YELLOW, "⚠"),
        "skip":    (CARD,  MUTED,  MUTED,  "—"),
    }

    def __init__(self, parent, icon, title, **kw):
        super().__init__(parent, bg=CARD, padx=14, pady=12,
                         highlightbackground=BORDER,
                         highlightthickness=1, **kw)
        self.icon_lbl  = tk.Label(self, text=icon, font=("Courier New", 20),
                                  bg=CARD, fg=MUTED)
        self.icon_lbl.pack()
        self.dot_lbl   = tk.Label(self, text="○", font=("Courier New", 12),
                                  bg=CARD, fg=MUTED)
        self.dot_lbl.pack()
        self.title_lbl = tk.Label(self, text=title, font=MF_B,
                                  bg=CARD, fg=MUTED)
        self.title_lbl.pack()
        self.count_lbl = tk.Label(self, text="", font=MF_S,
                                  bg=CARD, fg=MUTED)
        self.count_lbl.pack(pady=(4, 0))

    def set_state(self, state, count_text=""):
        _, title_c, dot_c, dot_sym = self.STATES.get(state, self.STATES["idle"])
        self.config(highlightbackground=dot_c if state != "idle" else BORDER)
        self.dot_lbl.config(text=dot_sym, fg=dot_c)
        self.title_lbl.config(fg=title_c)
        self.icon_lbl.config(fg=dot_c)
        self.count_lbl.config(text=count_text, fg=dot_c)


# ── Main App ──────────────────────────────────────────────────────────────────

class ScannerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Web App Vulnerability Scanner")
        self.geometry("1080x740")
        self.minsize(880, 620)
        self.configure(bg=BG)
        self._stop   = threading.Event()
        self._thread = None
        self._finds  = []
        self._build()

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build(self):
        self._top_bar()
        self._phase_row()
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")
        self._main_area()
        self._status_bar()

    # ── Top command bar ───────────────────────────────────────────────────────

    def _top_bar(self):
        bar = tk.Frame(self, bg=PANEL, pady=12, padx=16)
        bar.pack(fill="x")

        # Logo
        logo = tk.Frame(bar, bg=PANEL)
        logo.pack(side="left")
        tk.Label(logo, text="⚡", font=("Courier New", 22), bg=PANEL,
                 fg=ACC).pack(side="left")
        info = tk.Frame(logo, bg=PANEL)
        info.pack(side="left", padx=8)
        tk.Label(info, text="WEB VULNERABILITY SCANNER", font=MF_T,
                 bg=PANEL, fg=ACC).pack(anchor="w")
        tk.Label(info, text="SQL Injection  ·  XSS  ·  Security Headers",
                 font=MF_S, bg=PANEL, fg=MUTED).pack(anchor="w")

        # URL entry + buttons on right
        right = tk.Frame(bar, bg=PANEL)
        right.pack(side="right", fill="x", expand=True, padx=(30, 0))

        tk.Label(right, text="TARGET", font=MF_B, bg=PANEL,
                 fg=MUTED).pack(side="left")

        self.url_var = tk.StringVar(value="https://")
        url_e = tk.Entry(right, textvariable=self.url_var, width=34,
                         bg="#120e28", fg=TEXT, insertbackground=ACC,
                         font=MF, relief="flat", bd=6,
                         highlightbackground=BORDER, highlightthickness=1)
        url_e.pack(side="left", padx=8)

        self.scan_btn = pill_btn(right, "▶  SCAN", self._start, bg=ACC)
        self.scan_btn.pack(side="left", padx=(0, 6))

        self.stop_btn = pill_btn(right, "■  STOP", self._stop_scan,
                                 bg="#3b0764", fg=RED)
        self.stop_btn.pack(side="left", padx=(0, 6))
        self.stop_btn.config(state="disabled")

        pill_btn(right, "💾  EXPORT", self._export,
                 bg="#1e1b4b", fg=ACC2).pack(side="left")

    # ── Phase indicator row ───────────────────────────────────────────────────

    def _phase_row(self):
        row = tk.Frame(self, bg=BG, pady=14)
        row.pack(fill="x", padx=20)

        self._check_vars = {}
        phases = [
            ("🔒", "Headers",     "header"),
            ("💉", "SQL Inject.", "sqli"),
            ("📜", "XSS",        "xss"),
        ]

        self.phase_cards = {}
        for icon, title, key in phases:
            col = tk.Frame(row, bg=BG)
            col.pack(side="left", padx=8)

            card = PhaseCard(col, icon, title)
            card.pack()
            self.phase_cards[key] = card

            var = tk.BooleanVar(value=True)
            self._check_vars[key] = var
            cb = tk.Checkbutton(col, text="Enable", variable=var,
                                bg=BG, fg=MUTED, activebackground=BG,
                                activeforeground=ACC, selectcolor="#120e28",
                                font=MF_S, relief="flat", cursor="hand2")
            cb.pack(pady=(4, 0))

        # Separator
        tk.Frame(row, bg=BORDER, width=1).pack(side="left", fill="y", padx=16)

        # Options
        opt = tk.Frame(row, bg=BG)
        opt.pack(side="left", padx=8)
        tk.Label(opt, text="OPTIONS", font=MF_B, bg=BG, fg=MUTED).pack(anchor="w")

        dr = tk.Frame(opt, bg=BG)
        dr.pack(anchor="w", pady=4)
        tk.Label(dr, text="Delay (s):", font=MF_S, bg=BG, fg=MUTED).pack(side="left")
        self.delay_var = tk.StringVar(value="0.3")
        tk.Entry(dr, textvariable=self.delay_var, width=5, bg="#120e28",
                 fg=TEXT, insertbackground=ACC, font=MF, relief="flat",
                 bd=4).pack(side="left", padx=6)

        # Summary counters (right side of phase row)
        tk.Frame(row, bg=BORDER, width=1).pack(side="right", fill="y", padx=16)
        ctr = tk.Frame(row, bg=BG)
        ctr.pack(side="right", padx=8)
        tk.Label(ctr, text="FINDINGS", font=MF_B, bg=BG, fg=MUTED).pack(anchor="e")

        self.crit_lbl = tk.Label(ctr, text="CRITICAL  —", font=MF_B,
                                 bg=BG, fg=RED)
        self.crit_lbl.pack(anchor="e")
        self.high_lbl = tk.Label(ctr, text="HIGH      —", font=MF_B,
                                 bg=BG, fg=YELLOW)
        self.high_lbl.pack(anchor="e")
        self.med_lbl  = tk.Label(ctr, text="MEDIUM    —", font=MF_B,
                                 bg=BG, fg=ACC)
        self.med_lbl.pack(anchor="e")

    # ── Main content: table + terminal ───────────────────────────────────────

    def _main_area(self):
        pane = tk.PanedWindow(self, orient="horizontal", bg=BG,
                              sashwidth=4, sashrelief="flat",
                              sashpad=0, opaqueresize=True)
        pane.pack(fill="both", expand=True, padx=10, pady=8)

        # LEFT: findings table
        left = tk.Frame(pane, bg=BG)
        pane.add(left, minsize=380)
        self._findings_panel(left)

        # RIGHT: terminal log
        right = tk.Frame(pane, bg=BG)
        pane.add(right, minsize=300)
        self._terminal_panel(right)

        pane.paneconfigure(left,  width=560)
        pane.paneconfigure(right, width=380)

    def _findings_panel(self, parent):
        hdr = tk.Frame(parent, bg=BG)
        hdr.pack(fill="x", pady=(0, 4))
        tk.Label(hdr, text="VULNERABILITY FINDINGS", font=MF_B,
                 bg=BG, fg=ACC2).pack(side="left")
        self.find_count = tk.Label(hdr, text="[0 issues]", font=MF_S,
                                   bg=BG, fg=MUTED)
        self.find_count.pack(side="left", padx=8)

        cols = ("Severity", "Type", "Param", "URL")
        s = ttk.Style()
        s.theme_use("clam")
        s.configure("V.Treeview",
                    background=PANEL, foreground=TEXT,
                    fieldbackground=PANEL, rowheight=27, font=MF,
                    borderwidth=0)
        s.configure("V.Treeview.Heading",
                    background=CARD, foreground=ACC2,
                    font=MF_B, relief="flat")
        s.map("V.Treeview",
              background=[("selected", "#2d1b69")],
              foreground=[("selected", TEXT)])

        frm = tk.Frame(parent, bg=BORDER, highlightbackground=BORDER,
                       highlightthickness=1)
        frm.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(frm, columns=cols, show="headings",
                                  style="V.Treeview", selectmode="browse")
        for col, w, anchor in [("Severity",80,"center"),("Type",170,"w"),
                                ("Param",100,"w"),("URL",240,"w")]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor=anchor)

        vsb = ttk.Scrollbar(frm, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(frm, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        frm.rowconfigure(0, weight=1)
        frm.columnconfigure(0, weight=1)

        self.tree.tag_configure("critical", foreground=RED)
        self.tree.tag_configure("high",     foreground=YELLOW)
        self.tree.tag_configure("medium",   foreground=ACC)

        # Detail strip
        det = tk.Frame(parent, bg=CARD, pady=5, padx=8)
        det.pack(fill="x")
        self.det_lbl = tk.Label(det, text="▸ Select a row to see full details",
                                font=MF_S, bg=CARD, fg=MUTED, anchor="w",
                                wraplength=540, justify="left")
        self.det_lbl.pack(fill="x")
        self.tree.bind("<<TreeviewSelect>>", self._on_row)

    def _terminal_panel(self, parent):
        hdr = tk.Frame(parent, bg=BG)
        hdr.pack(fill="x", pady=(0, 4))
        tk.Label(hdr, text="// SCAN TERMINAL", font=MF_B,
                 bg=BG, fg=CYAN).pack(side="left")
        pill_btn(hdr, "CLR", self._clear_log,
                 bg=CARD, fg=MUTED).pack(side="right")

        term_frm = tk.Frame(parent, bg="#080510",
                            highlightbackground=CYAN,
                            highlightthickness=1)
        term_frm.pack(fill="both", expand=True)

        self.term = tk.Text(term_frm, bg="#080510", fg=GREEN,
                            font=("Courier New", 9), relief="flat",
                            state="disabled", insertbackground=GREEN,
                            wrap="word", padx=8, pady=8,
                            selectbackground="#2d1b69")
        tsb = ttk.Scrollbar(term_frm, orient="vertical",
                             command=self.term.yview)
        self.term.configure(yscrollcommand=tsb.set)
        self.term.pack(side="left", fill="both", expand=True)
        tsb.pack(side="right", fill="y")

        # tag colours
        self.term.tag_configure("banner", foreground=ACC,  font=("Courier New", 9, "bold"))
        self.term.tag_configure("phase",  foreground=CYAN, font=("Courier New", 9, "bold"))
        self.term.tag_configure("info",   foreground=GREEN)
        self.term.tag_configure("ok",     foreground=GREEN)
        self.term.tag_configure("warn",   foreground=YELLOW)
        self.term.tag_configure("vuln",   foreground=RED,  font=("Courier New", 9, "bold"))
        self.term.tag_configure("done",   foreground=ACC,  font=("Courier New", 9, "bold"))
        self.term.tag_configure("muted",  foreground=MUTED)
        self.term.tag_configure("error",  foreground=RED)

    def _status_bar(self):
        bar = tk.Frame(self, bg="#0a0718", pady=5)
        bar.pack(fill="x")
        self.status_var = tk.StringVar(value="◉  READY")
        tk.Label(bar, textvariable=self.status_var, font=MF_S,
                 bg="#0a0718", fg=MUTED).pack(side="left", padx=14)
        self.prog = ttk.Progressbar(bar, mode="indeterminate", length=160)
        self.prog.pack(side="right", padx=14, pady=2)

    # ── Scan control ──────────────────────────────────────────────────────────

    def _start(self):
        url = self.url_var.get().strip()
        if not url or url in ("http://", "https://"):
            messagebox.showwarning("No URL", "Please enter a target URL.")
            return
        if not url.startswith(("http://", "https://")):
            messagebox.showwarning("Invalid", "URL must start with http:// or https://")
            return
        try:
            delay = float(self.delay_var.get())
        except ValueError:
            delay = 0.3

        # Reset UI
        for r in self.tree.get_children():
            self.tree.delete(r)
        self._finds.clear()
        self.det_lbl.config(text="▸ Select a row to see full details")
        self.find_count.config(text="[0 issues]")
        self.crit_lbl.config(text="CRITICAL  —")
        self.high_lbl.config(text="HIGH      —")
        self.med_lbl.config( text="MEDIUM    —")
        self._clear_log()
        for card in self.phase_cards.values():
            card.set_state("idle")

        self._stop.clear()
        self.scan_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.prog.start(10)
        self.status_var.set("◉  SCANNING…")

        for line in [
            r"  _    _ _____ ____    ____  _____ ___  _   _ ",
            r" | |  | | ____| __ )  / ___|  |_ | __ \| \ | |",
            r" | |  | |  _| |  _ \  \___ \| |_ | | | |  \| |",
            r" | |__| | |___| |_) |  ___) |  _|| |_| | |\  |",
            r" |______|_____|____/  |____/|_|   \___/|_| \_|",
        ]:
            self._tlog(line, "banner")
        self._tlog("", "muted")
        self._tlog(f" Target : {url}", "muted")
        self._tlog(f" Time   : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "muted")
        self._tlog(" ─────────────────────────────────────────────", "muted")

        self._thread = threading.Thread(
            target=self._run, args=(url, delay), daemon=True)
        self._thread.start()

    def _run(self, url, delay):
        def log(msg, tag="info"):
            self.after(0, self._tlog, msg, tag)

        scanner = WebScanner(url, delay=delay,
                             log_callback=log, stop_flag=self._stop)

        if not self._stop.is_set() and self._check_vars["header"].get():
            self.after(0, self.phase_cards["header"].set_state, "active")
            log("► [PHASE 1] Security Header Analysis", "phase")
            scanner.check_headers()
            h_cnt = sum(1 for f in scanner.findings if "Header" in f["type"])
            self.after(0, self.phase_cards["header"].set_state,
                       "warn" if h_cnt else "done",
                       f"{h_cnt} missing" if h_cnt else "All present")
        else:
            self.after(0, self.phase_cards["header"].set_state, "skip")

        if not self._stop.is_set() and self._check_vars["sqli"].get():
            self.after(0, self.phase_cards["sqli"].set_state, "active")
            log("► [PHASE 2] SQL Injection Tests", "phase")
            scanner.sqli_url()
            scanner.sqli_forms(url)
            s_cnt = sum(1 for f in scanner.findings if "SQL" in f["type"])
            self.after(0, self.phase_cards["sqli"].set_state,
                       "warn" if s_cnt else "done",
                       f"{s_cnt} found" if s_cnt else "None found")
        else:
            self.after(0, self.phase_cards["sqli"].set_state, "skip")

        if not self._stop.is_set() and self._check_vars["xss"].get():
            self.after(0, self.phase_cards["xss"].set_state, "active")
            log("► [PHASE 3] XSS Tests", "phase")
            scanner.xss_url()
            scanner.xss_forms(url)
            x_cnt = sum(1 for f in scanner.findings if "XSS" in f["type"])
            self.after(0, self.phase_cards["xss"].set_state,
                       "warn" if x_cnt else "done",
                       f"{x_cnt} found" if x_cnt else "None found")
        else:
            self.after(0, self.phase_cards["xss"].set_state, "skip")

        self._finds = scanner.findings
        self.after(0, self._done)

    def _done(self):
        self.prog.stop()
        self.scan_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        n = len(self._finds)
        self.status_var.set(
            f"◉  DONE  —  {n} issue(s)  |  {datetime.now().strftime('%H:%M:%S')}")
        self._tlog(f" ─────────────────────────────────────────────", "muted")
        self._tlog(f" Scan complete. {n} issue(s) detected.", "done")
        self._populate_table()
        self._update_counters()

    def _stop_scan(self):
        self._stop.set()
        self.status_var.set("◉  STOPPING…")
        self.stop_btn.config(state="disabled")

    # ── Table & Log ──────────────────────────────────────────────────────────

    def _populate_table(self):
        for f in self._finds:
            sev, _ = SEVERITY.get(f["type"], ("INFO", MUTED))
            tag = {"CRITICAL": "critical", "HIGH": "high",
                   "MEDIUM": "medium"}.get(sev, "")
            short_url = (f["url"][:60] + "…") if len(f["url"]) > 62 else f["url"]
            self.tree.insert("", "end", tags=(tag,),
                             values=(sev, f["type"], f["param"], short_url))
        self.find_count.config(text=f"[{len(self._finds)} issue(s)]")

    def _update_counters(self):
        c = sum(1 for f in self._finds if "SQL"    in f["type"])
        h = sum(1 for f in self._finds if "XSS"    in f["type"])
        m = sum(1 for f in self._finds if "Header" in f["type"])
        self.crit_lbl.config(text=f"CRITICAL  {c}", fg=RED    if c else MUTED)
        self.high_lbl.config(text=f"HIGH      {h}", fg=YELLOW if h else MUTED)
        self.med_lbl.config( text=f"MEDIUM    {m}", fg=ACC    if m else MUTED)

    def _on_row(self, _):
        sel = self.tree.selection()
        if not sel:
            return
        idx = self.tree.index(sel[0])
        if idx < len(self._finds):
            f = self._finds[idx]
            self.det_lbl.config(
                text=f"URL: {f['url']}\nPayload: {f['payload']}"
                     + (f"\nDetail: {f['detail']}" if f.get("detail") else ""))

    def _tlog(self, msg, tag="info"):
        ts = datetime.now().strftime("%H:%M:%S")
        self.term.config(state="normal")
        prefix = "" if tag in ("banner", "muted") else f"[{ts}] "
        self.term.insert("end", f"{prefix}{msg}\n", tag)
        self.term.see("end")
        self.term.config(state="disabled")

    def _clear_log(self):
        self.term.config(state="normal")
        self.term.delete("1.0", "end")
        self.term.config(state="disabled")

    # ── Export ────────────────────────────────────────────────────────────────

    def _export(self):
        if not self._finds:
            messagebox.showinfo("Empty", "No findings to export. Run a scan first.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text", "*.txt"), ("All", "*.*")],
            initialfile=f"vuln_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        if not path:
            return
        with open(path, "w") as fh:
            fh.write("=" * 60 + "\n")
            fh.write("  WEB APP VULNERABILITY SCANNER — REPORT\n")
            fh.write(f"  Target : {self.url_var.get()}\n")
            fh.write(f"  Date   : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            fh.write(f"  Issues : {len(self._finds)}\n")
            fh.write("=" * 60 + "\n\n")
            for i, f in enumerate(self._finds, 1):
                sev, _ = SEVERITY.get(f["type"], ("INFO", ""))
                fh.write(f"[{i}] {sev} — {f['type']}\n")
                fh.write(f"    URL     : {f['url']}\n")
                fh.write(f"    Param   : {f['param']}\n")
                fh.write(f"    Payload : {f['payload']}\n")
                if f.get("detail"):
                    fh.write(f"    Detail  : {f['detail']}\n")
                fh.write("\n")
        messagebox.showinfo("Saved", f"Report saved:\n{path}")
        self._tlog(f"Report exported → {path}", "ok")


if __name__ == "__main__":
    app = ScannerApp()
    app.mainloop()
