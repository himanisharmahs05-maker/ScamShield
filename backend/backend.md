# Module 1: Link Intake, Sanitization & Normalization

> **Role in ScamShield:** The "bouncer and translator" — strips every attacker disguise and produces a clean, canonical URL before any security check runs.

---

## Why This Module Exists

A URL is just a string. Browsers are remarkably forgiving about how that string is formatted — they will happily decode triple-encoded characters, collapse weird paths, and silently substitute foreign-looking letters. Attackers exploit exactly this gap: they craft URLs that *look* harmless to a scanner but *behave* maliciously in a browser.

Module 1 closes that gap. Everything that enters the ScamShield pipeline passes through here first. What comes out is a mathematically canonical URL with all obfuscation removed, plus a list of any evasion flags raised during the process.

---

## Features

### 1. DoS Bomb Defuser — Length Enforcement

**Attacker trick:** Submit an absurdly long URL (tens of thousands of characters) to exhaust memory or trigger catastrophic regex backtracking inside the scanner.

**Fix:** Any input exceeding **2,048 characters** is rejected immediately before a single byte of processing occurs. The limit follows RFC 2616 / common browser caps and keeps the pipeline fast under adversarial load.

```
Input length > 2048 chars  →  REJECT (flagged as "Invalid/Suspicious")
```

---

### 2. Defanged URL Refanging

**Attacker trick (inverted):** Security researchers "defang" dangerous URLs when sharing them (`hxxp://evil[.]com`) so they aren't clickable. Users sometimes paste these into scanners — a naïve parser won't recognize them as URLs at all.

**Fix:** Before any other processing, the normalizer pattern-matches and rewrites defanged notation back to standard form:

| Defanged form | Normalized form |
|---|---|
| `hxxp://` | `http://` |
| `hxxps://` | `https://` |
| `evil[.]com` | `evil.com` |
| `evil(.)com` | `evil.com` |

---

### 3. Invisible Character Stripper

**Attacker trick:** Inject zero-width spaces (`U+200B`), soft hyphens (`U+00AD`), or other non-printable control characters (ASCII 0–31) into a domain. To a human the URL looks normal; to a blocklist lookup it's a completely different string.

**Fix:** A dedicated pass removes:
- All leading/trailing whitespace
- All non-printable ASCII control characters (0x00–0x1F)
- Unicode zero-width and invisible formatting characters

The result is a string that matches what a browser actually resolves.

---

### 4. Recursive Percent-Decode (Matryoshka Unwrapper)

**Attacker trick:** Standard percent-encoding maps a space to `%20`. Attackers *double-encode* the dangerous parts: `%` → `%25`, so `%20` becomes `%2520`. A scanner that decodes once sees `%20` (harmless); a browser decodes twice and sees the real payload.

**Fix:** Iterative decode loop — up to **5 passes** — comparing output to input each round:

```
while input != decoded AND iterations < 5:
    input = urllib.parse.unquote(input)
```

Convergence (input == output) means the true string is exposed. The iteration cap prevents infinite loops on pathological inputs.

---

### 5. Path Normalization (Directory Traversal Collapse)

**Attacker trick:** Hide a malicious destination behind a confusing path:
```
http://example.com/safe_folder/../../malware.exe
```
A scanner checking only the start of the path might see `/safe_folder/` and pass it. A browser resolves it to `/malware.exe`.

**Fix:** The path component is collapsed using POSIX path resolution semantics — the same logic browsers apply — so the canonical path always reflects the true destination:
```
/safe_folder/../../malware.exe  →  /malware.exe
```

---

### 6. Homograph Detection & Punycode Translation (Fake Alphabet Spotter)

**Attacker trick:** Buy `apple.com` where the `а` is Cyrillic (`U+0430`) not Latin (`a`). Visually identical; technically a different domain.

**Fix (two-part):**

1. **Punycode conversion** — Every hostname is encoded via Python's `idna` codec. The fake `apple.com` becomes `xn--pple-43d.com`, immediately exposing the impostor.

2. **Mixed-script detection** — After encoding, the normalizer checks whether the original hostname contained characters from more than one Unicode script block (e.g., Latin + Cyrillic). If so, a `MIXED_SCRIPT` warning flag is raised regardless of what the Punycode looks like.

```
apple.com (Cyrillic а)  →  xn--pple-43d.com  +  flag: MIXED_SCRIPT
```

---

### 7. Scheme & Port Standardization

**Attacker trick (passive):** `http://example.com:80/` and `http://example.com/` are the same URL. Without normalization, they produce different cache keys, different blocklist hits, and duplicate scan work.

**Fix:**
- Scheme is lowercased (`HTTP://` → `http://`)
- Default ports are stripped: `:80` on `http`, `:443` on `https`
- If no scheme is present, `http://` is assumed for analysis purposes
- The host (`netloc`) is lowercased for case-insensitive matching downstream

---

## Output Contract

Every URL that clears Module 1 produces a **NormalizedURL object**:

| Field | Type | Description |
|---|---|---|
| `canonical_url` | `str` | The fully normalized URL string |
| `scheme` | `str` | `http` or `https` |
| `host` | `str` | Lowercased, Punycode-encoded hostname |
| `path` | `str` | Collapsed, decoded path |
| `query` | `str` | Decoded query string |
| `flags` | `list[str]` | Any evasion indicators raised (e.g. `MIXED_SCRIPT`, `RECURSIVE_ENCODING_DETECTED`, `DEFANGED_INPUT`) |
| `rejected` | `bool` | `True` if the input was dropped before normalization (e.g. over length limit) |
| `rejection_reason` | `str \| None` | Human-readable rejection cause if `rejected=True` |

---

## Evasion Flags Reference

| Flag | Triggered by |
|---|---|
| `INPUT_TOO_LONG` | URL exceeded 2,048 character limit |
| `DEFANGED_INPUT` | Input matched defanged URL pattern |
| `INVISIBLE_CHARS_STRIPPED` | Non-printable characters were removed |
| `RECURSIVE_ENCODING_DETECTED` | More than one decode pass was required |
| `PATH_TRAVERSAL_COLLAPSED` | `..` sequences were resolved in the path |
| `MIXED_SCRIPT` | Hostname contained characters from multiple Unicode scripts |
| `PUNYCODE_CONVERTED` | Non-ASCII hostname was transliterated |

Flags are non-blocking by default — the normalized URL still proceeds to Module 2. Each flag carries a risk-score contribution that is picked up by the **Weighted Risk Fusion** engine in Module 8.

---

## Dependencies

| Library | Purpose |
|---|---|
| `urllib.parse` | URL splitting, percent-decoding, scheme normalization |
| `idna` | Punycode / IDNA encoding for homograph detection |
| `unicodedata` | Unicode script-block lookups for mixed-script detection |
| `re` | Defanging patterns, invisible character class matching |

---

## Related Modules

- **Module 2 →** Receives the canonical URL for link-type fingerprinting (IP links, shorteners, deep links)
- **Module 8 →** Consumes `flags` from this module as weighted penalty inputs into the final risk score

---

*ScamShield — Phase 1 Static Analysis Engine*

---

# Module 2: Heuristic Link Type Identification

> **Role in ScamShield:** The "fingerprinter" — classifies what a link is *trying to do* before judging whether it's good or bad.

---

## Why This Module Exists

Knowing a URL is malformed is one thing. Knowing *what it intends to do* is another. A link that opens a webpage is a fundamentally different threat surface than one that silently triggers a file download or forces a phone to open a banking app. Module 2 builds a behavioural profile of every link so that downstream scoring modules apply exactly the right threat logic — instead of treating every URL as just a generic web address.

Module 2 receives the clean `NormalizedURL` object from Module 1 and outputs a `LinkProfile` annotated with type classifications and any associated risk flags.

---

## Features

### 1. IP Address Detection & Obfuscation Unwrapping (The Numbers Game)

**Attacker trick:** Legitimate companies use domain names. Attackers use raw IP addresses (`http://192.168.1.1`) to bypass name-based blocklists entirely. To stay ahead of IP blocklists too, they encode the IP in alternative numeric formats — hexadecimal (`0x7f000001`), octal (`0177.0.0.1`), or plain 32-bit integer (`2130706433`) — all of which browsers resolve silently.

**Fix:** The host is tested against all four IP representations before falling back to domain classification:

| Format | Example | Detection method |
|---|---|---|
| Standard dotted decimal | `192.168.1.1` | `ipaddress.ip_address()` |
| Hexadecimal | `0xC0A80101` | Integer parse → `ip_address()` |
| Octal | `0300.0250.0.0` | Per-octet octal decode |
| Integer (dword) | `3232235520` | Direct `ip_address(int)` |

A match on any format raises `IP_BASED_LINK` and applies a high-risk penalty.

---

### 2. URL Shortener Detection (Unmasking the Mask)

**Attacker trick:** Services like `bit.ly`, `tinyurl.com`, and `t.co` completely hide the final destination of a link. Attackers use them to distribute links that appear innocuous while pointing to phishing pages or malware hosts.

**Fix:** The effective second-level domain (extracted via `tldextract`) is matched against a curated hash set of known shortener domains. A positive match raises `SHORTENED_URL` and signals Module 3 (Redirect Tracing) that resolving the final destination is mandatory, not optional.

---

### 3. Dangerous File Extension Detection (The Hidden Payload)

**Attacker trick:** Hide executable extensions not just at the end of the path, but inside query parameters — `http://example.com/download?file=malware.exe`. Scanners that check only the path suffix miss these entirely.

**Fix:** ScamShield inspects both the URL path and all query parameter *values* against a blocklist of high-risk extensions:

```
.exe  .apk  .dmg  .msi  .bat  .ps1  .scr  .vbs  .jar  .zip  .rar  .7z
```

Detection in either location raises `DIRECT_DOWNLOAD` with the matched extension recorded for the report.

---

### 4. Mobile Deep Link & Android Intent Parsing (Hijacking Your Phone)

**Attacker trick:** Non-HTTP schemes (`whatsapp://`, `tg://`, `zoommtg://`) bypass browser sandboxing entirely and directly invoke native apps. Android's `intent://` scheme is particularly dangerous — its fragment encodes a full package name and action, allowing an attacker to silently target a specific app (e.g., a banking app) with a crafted action.

**Fix:**

- Any non-`http`/`https` scheme raises `APP_DEEP_LINK` with the scheme recorded.
- For `intent://` URIs, the fragment (`#Intent;...`) is parsed to extract the `package=` and `scheme=` parameters. The resulting profile reports exactly which app is being targeted:

```
intent://scan/#Intent;scheme=zxing;package=com.google.zxing.client.android;end
→  flag: ANDROID_INTENT  |  target_package: com.google.zxing.client.android
```

---

### 5. Embedded Credential Detection (The Fake Login)

**Attacker trick:** Format a URL as `http://paypal.com@evil.com/`. Everything before `@` is treated by the browser as a username — `paypal.com` in this case — while the actual destination is `evil.com`. A victim glancing quickly sees a PayPal URL.

**Fix:** After parsing, the `userinfo` component of the URL (the `username:password@` prefix) is checked. Any non-empty `userinfo` field raises `EMBEDDED_CREDENTIALS`. Legitimate modern sites never embed credentials in public-facing links.

---

### 6. Dynamic DNS & Free Hosting Detection (Burner Domains)

**Attacker trick:** Free Dynamic DNS providers (`duckdns.org`, `ngrok.io`, `no-ip.com`, `trycloudflare.com`) let anyone spin up a live, reachable hostname in seconds at zero cost. When one gets blocked, a new one appears immediately. Real banks and businesses never use them.

**Fix:** The effective domain is matched against a maintained list of free Dynamic DNS and free-tunnel providers. A match raises `DYNAMIC_DNS` and contributes to the risk score — the combination of Dynamic DNS + any login keyword is treated as near-critical.

---

### 7. Dangerous Scheme & Raw File Host Detection (Hiding in Plain Sight)

**Attacker trick (two variants):**

- **Dangerous schemes:** `data:` and `javascript:` URIs embed their entire payload inside the URL string itself. No server is contacted; the malicious content executes locally in the browser the moment the link is opened.
- **Trusted-brand abuse:** Security scanners whitelist domains like `github.com` or `drive.google.com`. Attackers host malware there, knowing the brand name provides cover.

**Fix:**

- `data:` and `javascript:` schemes are detected during scheme normalization and raise `DANGEROUS_SCHEME` — these are hard-blocked regardless of any other signal.
- Known raw-file hosting paths (`raw.githubusercontent.com`, `drive.google.com/uc?export=download`, etc.) raise `RAW_FILE_HOST`, signalling that the *content* must be inspected rather than the domain's reputation.

---

## Output Contract

Module 2 produces a **LinkProfile object** appended to the existing scan context:

| Field | Type | Description |
|---|---|---|
| `link_types` | `list[str]` | All matched type classifications (e.g. `["SHORTENED_URL", "APP_DEEP_LINK"]`) |
| `flags` | `list[str]` | Risk flags raised during fingerprinting |
| `target_package` | `str \| None` | Android intent target package, if parsed |
| `detected_extension` | `str \| None` | Dangerous file extension found, if any |
| `userinfo_present` | `bool` | Whether embedded credentials were detected |
| `resolved_ip` | `str \| None` | Normalized IP string if host resolved to an IP format |

---

## Flags Reference

| Flag | Severity | Triggered by |
|---|---|---|
| `IP_BASED_LINK` | High | Host resolved to any IP format (decimal, hex, octal, integer) |
| `SHORTENED_URL` | Medium | Domain matched known shortener list |
| `DIRECT_DOWNLOAD` | High | Dangerous extension found in path or query params |
| `APP_DEEP_LINK` | Medium | Non-HTTP/HTTPS scheme detected |
| `ANDROID_INTENT` | High | `intent://` scheme with parseable package target |
| `EMBEDDED_CREDENTIALS` | High | Non-empty `userinfo` field in parsed URL |
| `DYNAMIC_DNS` | Medium | Domain matched free Dynamic DNS / tunnel provider list |
| `DANGEROUS_SCHEME` | Critical | `data:` or `javascript:` scheme detected |
| `RAW_FILE_HOST` | Medium | URL matched known raw-file hosting path pattern |

---

## Dependencies

| Library | Purpose |
|---|---|
| `ipaddress` | Standard, hex, octal, integer IP format validation |
| `tldextract` | Isolating effective second-level domain for list lookups |
| `urllib.parse` | Extracting scheme, userinfo, path, and query components |
| `re` | Android intent fragment parsing, file extension matching |

---

## Related Modules

- **Module 1 →** Provides the `NormalizedURL` input this module operates on
- **Module 3 →** `SHORTENED_URL` flag triggers mandatory redirect resolution
- **Module 4 →** `RAW_FILE_HOST` flag triggers content inspection
- **Module 8 →** All flags feed into the Weighted Risk Fusion scoring engine

---

*ScamShield — Phase 1 Static Analysis Engine*

---

# Module 3: Lightweight Redirect Tracing

> **Role in ScamShield:** The "private investigator" — follows every hop a link makes and returns the real final destination, not just the address on the envelope.

---

## Why This Module Exists

Imagine receiving a letter addressed from your local post office. Harmless, right? But inside is a note that says "go to this other address," which sends you to another address, which finally leads you to a shady building. That's exactly how redirect chains work.

Hackers rarely send victims directly to a malicious page anymore — that's too easy to block. Instead, they send a link that *looks* clean (sometimes even starting with a trusted domain like `google.com`), which automatically bounces the user through several intermediate websites in milliseconds before landing on the actual phishing page or malware. Standard scanners check the first address on the envelope and stop. Module 3 follows the chain all the way to the end.

> **Analogy:** Think of Module 3 as a detective who doesn't just read the address on a suspicious package — they physically follow it through every warehouse it passes through until they find out where it really ends up.

---

## Features

### 1. Disguising as a Real Human (User-Agent Masquerading)

**The trick:** Many hacker servers are smart. If they detect that a security bot is visiting their link rather than a real person, they show it a completely harmless page so the scanner marks the link as safe. The real attack page is only shown to actual victims.

**The fix:** ScamShield wears a disguise. Every network request it sends includes fake browser identity headers that make it look exactly like a real person using the latest version of Google Chrome on a Windows PC. The hacker's server can't tell the difference and serves up the real redirect chain.

```
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
            (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36
```

> **Simply put:** ScamShield wears a human mask so attackers don't hide the trap from it.

---

### 2. Catching Hidden Page Jumps (Client-Side Redirect Detection)

**The trick:** Standard redirect detection only catches server-level redirects — where a server explicitly says "go here instead" using HTTP codes like `301` or `302`. Attackers bypass this by hiding the redirect *inside the webpage's own code*, using:

- JavaScript: `window.location = "http://evil.com"`
- HTML meta tag: `<meta http-equiv="refresh" content="0; url=http://evil.com">`

A basic scanner downloads the page, sees a `200 OK` ("everything's fine"), and stops — completely missing the hidden jump buried in the source code.

**The fix:** After following server-level redirects, ScamShield reads the first **2,000 bytes** of the response body and scans it for these hidden redirect patterns. If found, it raises a flag and recommends a deeper Tier 2 scan.

| Pattern type | Example | Detected? |
|---|---|---|
| HTTP 301/302 | Server redirect header | ✅ Followed automatically |
| HTML meta refresh | `<meta http-equiv="refresh"...>` | ✅ Detected via text scan |
| JavaScript redirect | `window.location = "..."` | ✅ Detected via text scan |
| JS after user interaction | Button click triggers redirect | ⚠️ Requires Tier 2 (Phase 2) |

> **Simply put:** Most scanners only check the front door. ScamShield also peeks through the window to see if there's a hidden trapdoor inside.

---

### 3. Mapping Every Hop (Cross-Domain Redirect Tracking)

**The trick:** An attacker sends a link starting with `google.com/url?q=...`. Firewalls see "Google" and trust it. But the moment a victim clicks it, Google bounces them to `evil-phishing-site.com`. The firewall only saw the first hop and never checked where the chain ended.

**The fix:** ScamShield records every single domain visited along the chain, not just the first and last. It specifically watches for **cross-domain hops** — moments where the chain jumps to a completely unrelated website. A chain like:

```
google.com  →  legit-redirect.net  →  evil-phishing.xyz
```

...raises a `CROSS_DOMAIN_REDIRECT` flag. More than **3 total hops** is unusual for legitimate websites and is also flagged independently.

---

### 4. Escaping Infinite Mazes (Tarpit & Loop Defense)

**The trick:** Attackers use two techniques to disable scanners:

- **Redirect loops:** Site A → Site B → Site A → forever. The scanner spins in circles and crashes.
- **Tarpits:** A server accepts the connection but drip-feeds data one byte at a time, freezing the scanner.

**The fix:** ScamShield applies hard limits on both:

- **Max hops:** If the chain exceeds **10 redirects**, ScamShield stops and raises `REDIRECT_LOOP_SUSPECTED`.
- **Strict timeout:** If any server takes too long to respond, the connection is cut and flagged as `TARPIT_SUSPECTED`.
- **Stream mode:** ScamShield requests only the *headers* of each page, refusing to download the full response body — so a 10 GB file can't stall the pipeline.

> **Simply put:** ScamShield gives every server a strict time limit and a maximum number of chances. Stall or loop, and it cuts the cord.

---

### 5. Detecting Anti-Scanner Shields (WAF & CAPTCHA Detection)

**The trick:** Sophisticated phishing sites protect their pages with Cloudflare's "Just a moment..." screen or a CAPTCHA puzzle. A human solves it easily; a security bot cannot. The bot never sees the phishing page and incorrectly marks the site as safe.

**The fix:** ScamShield inspects HTTP response headers and status codes at each hop for known anti-bot signatures:

- HTTP `403 Forbidden` or `429 Too Many Requests` from known WAF providers
- Cloudflare challenge headers (`cf-mitigated: challenge`)
- Known CAPTCHA phrases in the response body

When detected, a `WAF_SHIELDED` flag is raised. This tells the scoring engine: *"We couldn't see the full payload — something is deliberately hiding it from automated tools."* Tier 2 analysis is recommended.

---

## Output Contract

Module 3 appends a **RedirectTrace object** to the scan context:

| Field | Type | Description |
|---|---|---|
| `final_url` | `str` | The true last URL in the redirect chain |
| `final_domain` | `str` | Extracted domain of the final destination |
| `hop_count` | `int` | Total number of redirects followed |
| `chain` | `list[str]` | Ordered list of every URL visited |
| `cross_domain_hops` | `int` | Number of times the domain changed mid-chain |
| `client_side_redirect` | `bool` | Whether a JS or meta-refresh redirect was detected |
| `flags` | `list[str]` | Risk flags raised during tracing |

---

## Flags Reference

| Flag | Severity | Triggered by |
|---|---|---|
| `CROSS_DOMAIN_REDIRECT` | Medium | Domain changed one or more times during the chain |
| `HIGH_HOP_COUNT` | Medium | More than 3 redirects followed |
| `CLIENT_SIDE_REDIRECT` | Medium | JS `window.location` or `<meta refresh>` detected in body |
| `REDIRECT_LOOP_SUSPECTED` | High | Chain exceeded 10 hops without a final page |
| `TARPIT_SUSPECTED` | High | Server response timed out during tracing |
| `WAF_SHIELDED` | High | Anti-bot challenge or WAF block detected at destination |

---

## Dependencies

| Library | Purpose |
|---|---|
| `httpx` / `requests` | Following HTTP redirects with stream mode and custom headers |
| `tldextract` | Extracting and comparing domains at each hop |
| `re` | Scanning response body for client-side redirect patterns |

---

## Related Modules

- **Module 2 →** `SHORTENED_URL` flag makes this module's execution mandatory
- **Module 5 →** `final_url` is passed to Domain Reputation as the true target domain
- **Module 6 →** `final_domain` feeds into Lexical Analysis for typosquatting checks
- **Module 8 →** All flags feed into the Weighted Risk Fusion scoring engine

---

*ScamShield — Phase 1 Static Analysis Engine*