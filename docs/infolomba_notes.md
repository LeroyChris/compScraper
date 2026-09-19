# Discovery & Inspection Report: `infolomba.id`

Based on the inspection script run against `infolomba.id`, here is the breakdown of the site's structure, rendering logic, and anti-scraping measures.

## 1. Rendering Architecture
- **Event List Page (SSR):** The initial list of events is rendered **Server-Side**. The HTML comes fully populated with event cards (`class="event-container"`).
- **Detail Pages (AJAX / CSR):** 
  - Clicking on an event card does not trigger a full page navigation. Instead, it fires an inline JS function: `onclick="loadDetailsEvent(eventId, 'eventSEO', this)"`.
  - This function triggers an `XMLHttpRequest` (POST) to `/load-details` with the payload `event_id=XXXX`.
  - The server responds with a JSON object containing a raw HTML string `{"html": "<div..."}`, which is then dynamically injected into an overlay modal on the client side.
  - **Direct SEO URLs:** The site also supports direct navigation via URLs formatted as `https://infolomba.id/{seo-slug}-{eventId}`.

## 2. CSS Selectors & DOM Structures
We extracted the exact DOM footprint to be used in the Phase 2 scraper pipeline.

### List Items (Cards)
- **Container:** `<div class="event-container">`
- **Title:** `<h4 class="event-title">`
- **Click Handler / Event ID:** Located in `onclick="loadDetailsEvent(2128, 'info-business-plan...', this)"`
- **Card Fields:** 
  - Fee: `<div class="biaya">`
  - Location: `<div class="lokasi">`
  - Date: `<div class="tanggal">`
  - Organizer: `<div class="penyelenggara">`

### Pagination
- Triggered by a button bound to a Javascript function.
- Sends an AJAX **POST** request to `/load-event-2` passing multiple form data parameters (`start`, `sort`, `title`, `peserta`, etc.).
- The server responds with raw HTML payload which is appended to the list container.

## 3. Basic Protection Measures
- **Cloudflare / WAF:** No evidence of Cloudflare or strict WAF rate limits in the headers.
- **Server:** `LiteSpeed`.
- **Bot Mitigation:** Minimal. The site relies on a standard session cookie (`JMWPHP`) but does not challenge requests that lack Javascript execution, provided standard browser `User-Agent` and headers are sent.
- **Header Sensitivity:** The server sends compressed responses (Brotli `br`) if requested. Ensure HTTP clients (like `requests`) are configured properly (e.g., omitting `br` in `Accept-Encoding` unless a library like `brotli` is installed) to prevent decoding failures.

## 4. How to Run the Discovery Script
We built a lightweight `requests`-based inspection script that mimics a real browser and safely pulls list data and dynamically queries the detail API.

**To run the script:**
```bash
python3 inspect_infolomba.py
```

**What to expect in the output:**
1. **Logs:** Verbose CLI output showing HTTP codes, HTML sizes, and extracted data.
2. **`debug_list_page.html`:** The raw SSR HTML of the target filtered list.
3. **`debug_detail_api.json`:** The raw JSON response from the `/load-details` POST API.
4. **`debug_detail_page.html`:** The HTML cleanly extracted from the JSON response for manual CSS mapping.
5. **`inspection_report.json`:** A structured summary of the extraction process.

## Next Steps
With the structure fully documented, Phase 2 can proceed using standard HTTP POST requests to navigate pagination (`/load-event-2`) and extract detailed data (`/load-details`) seamlessly without needing a heavy headless browser like Playwright/Selenium.
