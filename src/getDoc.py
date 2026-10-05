import requests
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright


PDF_MAGIC = b"%PDF-"

# hrefs that are not navigable documents.
SKIPPED_HREF_PREFIXES = ("mailto:", "tel:", "javascript:", "#")

NAV_TIMEOUT_MS = 30000
CLICK_TIMEOUT_MS = 10000
NAVIGATION_GRACE_MS = 3000   # how long to wait for the click to visibly do something
POPUP_URL_WAIT_MS = 10000    # how long a new tab may sit on about:blank
POLL_MS = 100


# ----------------------------------------------------------------
# PDF helpers
# ----------------------------------------------------------------

def is_pdf_bytes(content):
    """
    A PDF header may be preceded by a few bytes of junk or whitespace;
    the spec allows it anywhere in the first 1024 bytes.
    """
    return bool(content) and PDF_MAGIC in content[:1024]


def has_eof_marker(content):
    """Cheap completeness hint: valid PDFs end with %%EOF."""
    return b"%%EOF" in content[-2048:]


def build_document(name, source_url, final_url, content, content_type, method):
    return {
        "source_url": source_url,
        "name": name,
        "final_url": final_url,
        "content": content,
        "content_type": content_type,
        "is_pdf": True,
        "has_eof": has_eof_marker(content),
        "retrieval_method": method,
    }


def failure(name, url, reason):
    return {"name": name, "url": url, "reason": reason}


# ----------------------------------------------------------------
# Page helpers
# ----------------------------------------------------------------

def open_page(page, url):
    """Open a page and wait for it to settle (raises if it cannot load)."""
    page.goto(url, wait_until="domcontentloaded", timeout=NAV_TIMEOUT_MS)

    try:
        page.wait_for_load_state("networkidle", timeout=5000)
    except Exception:
        pass


def is_ui_link(link):
    """Check whether a link is inside a header/nav/footer/aside."""
    return link.locator(
        "xpath="
        "ancestor::header | "
        "ancestor::nav | "
        "ancestor::footer | "
        "ancestor::aside"
    ).count() > 0


def resolve_href(link, base_url):
    """Absolute URL for a link, or None if it is not a navigable href."""
    href = link.get_attribute("href")

    if not href:
        return None

    href = href.strip()

    if not href or href.lower().startswith(SKIPPED_HREF_PREFIXES):
        return None

    return urljoin(base_url, href)


def iter_page_links(page, base_url):
    """Yield (link, url, name) for every non-UI, navigable link, in page order."""
    links = page.locator("a[href]")

    for i in range(links.count()):
        link = links.nth(i)

        if is_ui_link(link):
            continue

        url = resolve_href(link, base_url)

        if url is None:
            continue

        yield link, url, link.inner_text().strip()


def collect_candidates(page, base_url):
    """
    All links in page order. Each is tagged with which occurrence of its
    name it is (1st "Notice A", 2nd "Notice A", ...).
    """
    counts = {}
    candidates = []

    for _, url, name in iter_page_links(page, base_url):
        counts[name] = counts.get(name, 0) + 1

        candidates.append({
            "url": url,
            "name": name,
            "occurrence": counts[name],
        })

    return candidates


def find_link_by_name(page, base_url, name, occurrence):
    """Return the Nth link (1-based) whose text equals name, or None."""
    count = 0

    for link, _, link_name in iter_page_links(page, base_url):

        if link_name != name:
            continue

        count += 1

        if count == occurrence:
            return link

    return None


def find_notice_link(page, base_url, notice, occurrence):
    """
    Match by name and sequence only (no URL matching). The occurrence
    counts across ALL notices sharing that name, not just HTTP failures.
    """
    return find_link_by_name(page, base_url, notice["name"], occurrence)


# ----------------------------------------------------------------
# Browser PDF detection
# ----------------------------------------------------------------

def click_and_get_pdf(context, page, link):
    """
    Click a link, then judge ONLY what the browser ends up displaying.

    1. Click the link like a user would.
    2. Wait for the browser to react: a new tab opens, or the current
       page navigates. The last tab opened (or the current page) is the
       "final display".
    3. Wait for that page to finish loading.
    4. Ask the browser what the final display is (document.contentType).
       If it is not a PDF, stop here.
    5. If it is a PDF, fetch the final URL through the browser context
       (same cookies/session) to obtain the bytes, and confirm them.

    Network traffic that happened along the way is ignored.

    Returns (final_url, content, content_type, reason).
    reason is None on success.
    """
    opened_pages = []
    navigation_responses = []

    def on_page(new_page):
        opened_pages.append(new_page)

    def on_response(response):
        # Only remember page navigations; bodies are read later, and
        # only for the response matching the final display.
        try:
            if response.request.is_navigation_request():
                navigation_responses.append(response)
        except Exception:
            pass

    context.on("page", on_page)
    context.on("response", on_response)

    url_before = page.url

    try:

        # A failed click is reported as a failed click.
        try:
            link.click(timeout=CLICK_TIMEOUT_MS)
        except Exception as error:
            return None, None, None, f"click_failed: {error}"

        # Wait for the browser to react (new tab or URL change).
        waited = 0

        while waited < NAVIGATION_GRACE_MS:

            if opened_pages or page.url != url_before:
                break

            page.wait_for_timeout(POLL_MS)
            waited += POLL_MS

        final_page = opened_pages[-1] if opened_pages else page

        # A new tab starts on about:blank before it navigates.
        if final_page is not page:

            waited = 0

            while (
                final_page.url in ("", "about:blank")
                and waited < POPUP_URL_WAIT_MS
            ):
                final_page.wait_for_timeout(POLL_MS)
                waited += POLL_MS

        try:
            final_page.wait_for_load_state(
                "load",
                timeout=NAV_TIMEOUT_MS
            )
        except Exception:
            pass

        final_url = final_page.url

        if not final_url or final_url == "about:blank":
            return None, None, None, "no_final_page"

        # What is the browser actually displaying?
        display_type = None

        try:
            display_type = final_page.evaluate("document.contentType")
        except Exception:
            pass

        if (
            display_type is not None
            and "application/pdf" not in display_type.lower()
        ):
            return None, None, display_type, f"display_not_pdf: {display_type}"

        # The browser is showing a PDF (or its type could not be read).
        # Get the bytes.
        content = None
        content_type = ""
        fetch_error = None

        # 1) The browser's OWN response for the final URL. This is
        #    exactly what it received, so it works for session-bound or
        #    one-time URLs.
        for response in reversed(navigation_responses):

            if response.url != final_url:
                continue

            try:
                body = response.body()
            except Exception:
                continue

            if is_pdf_bytes(body):
                content = body
                content_type = response.headers.get("content-type", "")
                break

        # 2) Fallback: request the final URL again through the browser
        #    session, with the page we clicked from as Referer.
        if content is None:

            try:

                fetched = context.request.get(
                    final_url,
                    headers={"Referer": url_before},
                    timeout=NAV_TIMEOUT_MS
                )

                body = fetched.body()

                if is_pdf_bytes(body):
                    content = body
                    content_type = fetched.headers.get("content-type", "")

            except Exception as error:
                fetch_error = str(error)

        if content is None:

            reason = "bytes_not_pdf"

            if fetch_error:
                reason += f" (refetch error: {fetch_error})"

            return None, None, display_type, reason

        return final_url, content, content_type, None

    finally:

        try:
            context.remove_listener("page", on_page)
            context.remove_listener("response", on_response)
        except Exception:
            pass

        # Always close tabs opened by the click.
        for opened in opened_pages:
            try:
                opened.close()
            except Exception:
                pass


def click_to_document(context, page, link, name, source_url):
    """Click a link; return (document, None) or (None, reason)."""
    final_url, content, content_type, reason = click_and_get_pdf(
        context, page, link
    )

    if content is None:
        return None, reason

    document = build_document(
        name, source_url, final_url, content, content_type, "browser"
    )

    return document, None


# ----------------------------------------------------------------
# Browser modes
# ----------------------------------------------------------------

def discover_and_retrieve(context, page, notices_url, documents, failed_notices):
    """
    MODE 1 - no notices known: discover links on the homepage and click
    each one in page order. Links that do not yield a PDF are reported
    in failed_notices with a reason.
    """
    print("[Browser] Discovering links")

    candidates = collect_candidates(page, notices_url)

    print(f"[Browser] Found {len(candidates)} candidate links")

    for candidate in candidates:

        target_url = candidate["url"]
        name = candidate["name"]

        print(f"[Browser] Processing: {name or target_url}")

        try:

            if page.url != notices_url:
                open_page(page, notices_url)

            link = find_link_by_name(
                page, notices_url, name, candidate["occurrence"]
            )

            if link is None:
                print("[Browser] Link not found")
                failed_notices.append(
                    failure(name, target_url, "link_not_found")
                )
                continue

            document, reason = click_to_document(
                context, page, link, name, target_url
            )

        except Exception as error:
            print(f"[Browser] Failed: {name or target_url}: {error}")
            failed_notices.append(
                failure(name, target_url, f"error: {error}")
            )
            continue

        if document is None:
            print(f"[Browser] No PDF ({reason})")
            failed_notices.append(failure(name, target_url, reason))
            continue

        documents.append(document)
        print("[Browser] PDF found")


def retrieve_failed(context, page, notices_url, browser_needed,
                    documents, failed_notices):
    """
    MODE 2 - notices known but HTTP failed for some: locate each link
    (URL match first, then name + occurrence) and click it.
    """
    for notice, occurrence in browser_needed:

        name = notice["name"]
        url = notice["url"]

        print(f"[Browser] Processing: {name} ({occurrence})")

        reason = None
        document = None

        try:

            if page.url != notices_url:
                open_page(page, notices_url)

            link = find_notice_link(page, notices_url, notice, occurrence)

            if link is None:
                reason = "link_not_found"
                print("[Browser] Matching link not found")
            else:
                document, reason = click_to_document(
                    context, page, link, name, url
                )

        except Exception as error:
            reason = f"error: {error}"
            print(f"[Browser] Failed: {name}: {error}")

        if document is not None:
            documents.append(document)
            print("[Browser] PDF found")
        else:
            print(f"[Browser] No PDF ({reason})")
            failed_notices.append({**notice, "reason": reason})


# ----------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------

def documentRetrieval(notices, notices_url, headless=False):
    """
    Retrieve documents for notices.

    HTTP retrieval is attempted first. Notices that fail it are opened
    through the browser by actually clicking their links. If no notices
    are supplied, the browser discovers candidate links from the notices
    homepage.

    Returns:
        documents:
            Successfully retrieved PDFs.

        failed_notices:
            Notices (or discovered links) that could not be retrieved,
            each with a "reason".
    """

    documents = []
    failed_notices = []

    headers = {"User-Agent": "Mozilla/5.0"}

    # Occurrence of each name across ALL notices, so duplicate names
    # still map to the right link even if earlier ones succeeded.
    name_counts = {}
    indexed_notices = []

    for notice in notices:
        count = name_counts.get(notice["name"], 0) + 1
        name_counts[notice["name"]] = count
        indexed_notices.append((notice, count))

    # ============================================================
    # STEP 1 - HTTP RETRIEVAL
    # ============================================================

    browser_needed = []

    for notice, occurrence in indexed_notices:

        name = notice["name"]
        url = notice["url"]

        try:

            response = requests.get(
                url,
                headers=headers,
                timeout=15,
                allow_redirects=True,
            )

            response.raise_for_status()

            content = response.content

            if is_pdf_bytes(content):

                documents.append(build_document(
                    name,
                    url,
                    response.url,
                    content,
                    response.headers.get("Content-Type", ""),
                    "http",
                ))

                print(f"[HTTP] Retrieved: {name}")

            else:
                browser_needed.append((notice, occurrence))

        except requests.RequestException:
            browser_needed.append((notice, occurrence))

    # If all HTTP retrievals succeeded, the browser isn't needed.
    if notices and not browser_needed:
        return documents, failed_notices

    # ============================================================
    # STEP 2 - BROWSER
    # ============================================================

    print("[Browser] Starting")

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=headless)

        try:

            context = browser.new_context()
            page = context.new_page()

            try:

                open_page(page, notices_url)
                print("[Browser] Page loaded")

            except Exception as error:

                print(f"[Browser] Failed to open page: {error}")

                for notice, _ in browser_needed:
                    failed_notices.append(
                        {**notice, "reason": f"homepage_unavailable: {error}"}
                    )

                return documents, failed_notices

            if not notices:
                discover_and_retrieve(
                    context, page, notices_url, documents, failed_notices
                )
            else:
                retrieve_failed(
                    context, page, notices_url, browser_needed,
                    documents, failed_notices
                )

        finally:

            try:
                browser.close()
            except Exception:
                pass

    return documents, failed_notices