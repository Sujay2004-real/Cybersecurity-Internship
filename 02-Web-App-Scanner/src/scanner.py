"""
Web Application Vulnerability Scanner
Detects: SQL Injection, XSS, Missing Security Headers
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlencode, parse_qs, urlunparse
import time

# ── Payloads ──────────────────────────────────────────────────────────────────

SQLI_PAYLOADS = [
    "'",
    "''",
    "' OR '1'='1",
    "' OR '1'='1' --",
    "' OR 1=1 --",
    "\" OR \"1\"=\"1",
    "1' ORDER BY 1--",
    "1' ORDER BY 2--",
    "1 UNION SELECT NULL--",
    "' AND SLEEP(0)--",
]

SQLI_ERRORS = [
    "you have an error in your sql syntax",
    "warning: mysql",
    "unclosed quotation mark",
    "quoted string not properly terminated",
    "sql syntax",
    "sqlstate",
    "odbc driver",
    "ora-01756",
    "sqlite3.operationalerror",
    "pg::syntaxerror",
    "syntax error in query expression",
    "microsoft ole db provider for sql server",
    "invalid query",
    "supplied argument is not a valid mysql",
]

XSS_PAYLOADS = [
    "<script>alert('XSS')</script>",
    "<img src=x onerror=alert('XSS')>",
    "<svg onload=alert('XSS')>",
    "\"><script>alert('XSS')</script>",
    "'><script>alert('XSS')</script>",
    "<body onload=alert('XSS')>",
    "<iframe src=\"javascript:alert('XSS')\">",
]

SECURITY_HEADERS = {
    "Content-Security-Policy":    "Prevents XSS and data injection attacks",
    "X-Content-Type-Options":     "Stops MIME-type sniffing",
    "X-Frame-Options":            "Prevents clickjacking",
    "Strict-Transport-Security":  "Enforces HTTPS (HSTS)",
    "Referrer-Policy":            "Controls referrer information leakage",
    "Permissions-Policy":         "Limits browser feature access",
    "X-XSS-Protection":           "Legacy XSS browser filter",
}

# ── Scanner ───────────────────────────────────────────────────────────────────

class WebScanner:
    def __init__(self, target_url: str, timeout: int = 8,
                 delay: float = 0.3, log_callback=None, stop_flag=None):
        self.target   = target_url.rstrip("/")
        self.timeout  = timeout
        self.delay    = delay
        self.log      = log_callback or print
        self.stop     = stop_flag          # threading.Event
        self.session  = requests.Session()
        self.session.headers.update({
            "User-Agent": "WebAppScanner/1.0 (Educational Security Tool)"
        })
        self.findings = []

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _get(self, url, params=None):
        try:
            r = self.session.get(url, params=params,
                                 timeout=self.timeout, allow_redirects=True)
            return r
        except requests.RequestException as e:
            self.log(f"[!] Request error: {e}", "warn")
            return None

    def _post(self, url, data):
        try:
            r = self.session.post(url, data=data,
                                  timeout=self.timeout, allow_redirects=True)
            return r
        except requests.RequestException as e:
            self.log(f"[!] Request error: {e}", "warn")
            return None

    def _add(self, vuln_type, url, param, payload, detail=""):
        self.findings.append({
            "type":    vuln_type,
            "url":     url,
            "param":   param,
            "payload": payload,
            "detail":  detail,
        })

    def _stopped(self):
        return self.stop is not None and self.stop.is_set()

    # ── Crawl forms ───────────────────────────────────────────────────────────

    def get_forms(self, url):
        r = self._get(url)
        if not r:
            return []
        soup = BeautifulSoup(r.content, "html.parser")
        return soup.find_all("form")

    def form_details(self, form):
        action  = form.attrs.get("action", "").strip()
        method  = form.attrs.get("method", "get").lower()
        inputs  = []
        for inp in form.find_all(["input", "textarea", "select"]):
            inputs.append({
                "type":  inp.attrs.get("type", "text"),
                "name":  inp.attrs.get("name"),
                "value": inp.attrs.get("value", ""),
            })
        return {"action": action, "method": method, "inputs": inputs}

    # ── Security Headers ──────────────────────────────────────────────────────

    def check_headers(self):
        self.log("Checking security headers…", "info")
        r = self._get(self.target)
        if not r:
            return
        found_any = False
        for header, desc in SECURITY_HEADERS.items():
            if header.lower() not in {k.lower() for k in r.headers}:
                self.log(f"  Missing: {header} — {desc}", "warn")
                self._add("Missing Header", self.target, header, "N/A", desc)
                found_any = True
        if not found_any:
            self.log("  All security headers present ✔", "ok")

    # ── URL param SQLi ────────────────────────────────────────────────────────

    def sqli_url(self):
        parsed = urlparse(self.target)
        params = parse_qs(parsed.query)
        if not params:
            self.log("  No URL parameters found for SQLi testing.", "muted")
            return

        for param in params:
            for payload in SQLI_PAYLOADS:
                if self._stopped(): return
                test_params = {k: v[0] for k, v in params.items()}
                test_params[param] = payload
                new_query = urlencode(test_params)
                test_url  = urlunparse(parsed._replace(query=new_query))
                r = self._get(test_url)
                if r:
                    body = r.text.lower()
                    for err in SQLI_ERRORS:
                        if err in body:
                            self.log(f"  [VULN] SQLi in param '{param}' → {payload[:30]}", "vuln")
                            self._add("SQL Injection", test_url, param,
                                      payload, f"DB error: {err}")
                            break
                time.sleep(self.delay)

    # ── Form SQLi ─────────────────────────────────────────────────────────────

    def sqli_forms(self, url):
        forms = self.get_forms(url)
        self.log(f"  Found {len(forms)} form(s) on {url}", "info")
        for form in forms:
            d = self.form_details(form)
            action = urljoin(url, d["action"]) if d["action"] else url
            for payload in SQLI_PAYLOADS:
                if self._stopped(): return
                data = {}
                for inp in d["inputs"]:
                    if inp["name"]:
                        data[inp["name"]] = payload if inp["type"] != "hidden" else inp["value"]
                r = self._post(action, data) if d["method"] == "post" else self._get(action, data)
                if r:
                    body = r.text.lower()
                    for err in SQLI_ERRORS:
                        if err in body:
                            self.log(f"  [VULN] SQLi in form → {action} | payload: {payload[:30]}", "vuln")
                            self._add("SQL Injection (Form)", action,
                                      str(list(data.keys())), payload, f"DB error: {err}")
                            break
                time.sleep(self.delay)

    # ── XSS URL params ────────────────────────────────────────────────────────

    def xss_url(self):
        parsed = urlparse(self.target)
        params = parse_qs(parsed.query)
        if not params:
            self.log("  No URL parameters found for XSS testing.", "muted")
            return

        for param in params:
            for payload in XSS_PAYLOADS:
                if self._stopped(): return
                test_params = {k: v[0] for k, v in params.items()}
                test_params[param] = payload
                new_query = urlencode(test_params)
                test_url  = urlunparse(parsed._replace(query=new_query))
                r = self._get(test_url)
                if r and payload in r.text:
                    self.log(f"  [VULN] Reflected XSS in param '{param}'", "vuln")
                    self._add("Reflected XSS", test_url, param, payload)
                    break
                time.sleep(self.delay)

    # ── XSS Forms ─────────────────────────────────────────────────────────────

    def xss_forms(self, url):
        forms = self.get_forms(url)
        for form in forms:
            d = self.form_details(form)
            action = urljoin(url, d["action"]) if d["action"] else url
            for payload in XSS_PAYLOADS:
                if self._stopped(): return
                data = {}
                for inp in d["inputs"]:
                    if inp["name"]:
                        data[inp["name"]] = payload if inp["type"] != "hidden" else inp["value"]
                r = self._post(action, data) if d["method"] == "post" else self._get(action, data)
                if r and payload in r.text:
                    self.log(f"  [VULN] Reflected XSS in form → {action}", "vuln")
                    self._add("Reflected XSS (Form)", action,
                              str(list(data.keys())), payload)
                    break
                time.sleep(self.delay)

    # ── Full Scan ─────────────────────────────────────────────────────────────

    def run(self):
        self.findings.clear()

        self.log(f"Target: {self.target}", "info")
        self.log("─" * 55, "muted")

        # 1. Headers
        self.log("► Phase 1: Security Header Analysis", "phase")
        self.check_headers()
        if self._stopped(): return self.findings

        # 2. SQLi
        self.log("► Phase 2: SQL Injection Tests", "phase")
        self.sqli_url()
        self.sqli_forms(self.target)
        if self._stopped(): return self.findings

        # 3. XSS
        self.log("► Phase 3: Cross-Site Scripting (XSS) Tests", "phase")
        self.xss_url()
        self.xss_forms(self.target)

        self.log("─" * 55, "muted")
        self.log(f"Scan complete. {len(self.findings)} issue(s) found.", "done")
        return self.findings


if __name__ == "__main__":
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else "http://example.com"
    scanner = WebScanner(url)
    results = scanner.run()
    print(f"\n=== {len(results)} findings ===")
    for f in results:
        print(f"  [{f['type']}] {f['url']} | param={f['param']}")
