import re
import time
import json
import html as _html
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

def fetch_html(url: str) -> str:
    """
    Fetch HTML using requests with broad headers, then unescape all HTML entities
    so hidden emails (&#64;, &commat;, etc.) become real characters.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    }
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 406:
            headers['Accept'] = '*/*'
            res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        raw = res.text
        # full unescape of all HTML entities
        return _html.unescape(raw)
    except Exception as e:
        print(f"[fetch_html] error {getattr(e, 'response', '')} {e} at {url}")
        return ""

def extract_emails_from_text(text: str) -> set[str]:
    """
    Run regex over both the visible text and the raw HTML to find email addresses.
    """
    # deobfuscate common patterns
    deobs = (
        text
        .replace('[at]', '@').replace('(at)', '@').replace(' at ', '@')
        .replace('[dot]', '.').replace('(dot)', '.')
    )
    combined = text + "\n" + deobs
    pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    return set(re.findall(pattern, combined, flags=re.IGNORECASE))

def extract_emails_from_soup(soup) -> set[str]:
    """
    Find emails in mailto: links, aria-labels, and JSON-LD structured data.
    """
    mails = set()

    # 1) mailto: links
    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.lower().startswith('mailto:'):
            addr = href.split(':', 1)[1].split('?')[0]
            mails.add(addr)

    # 2) aria-label attributes containing "@"
    for tag in soup.find_all(attrs={"aria-label": True}):
        label = tag['aria-label']
        if "@" in label:
            mails |= extract_emails_from_text(label)

    # 3) JSON-LD blocks
    for s in soup.find_all("script", {"type": "application/ld+json"}):
        try:
            data = json.loads(s.string or "{}")
        except json.JSONDecodeError:
            continue

        def scan(obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if k.lower() == "email" and isinstance(v, str) and "@" in v:
                        mails.add(v)
                    else:
                        scan(v)
            elif isinstance(obj, list):
                for item in obj:
                    scan(item)

        scan(data)

    return mails

def is_internal_link(href: str, base: str) -> bool:
    """
    Only follow HTTP(S) links on the same domain; skip tel:, mailto:, javascript:, etc.
    """
    if not href:
        return False
    parsed = urlparse(href)
    if parsed.scheme and parsed.scheme not in ("http", "https"):
        return False
    full = urljoin(base, href)
    return urlparse(full).netloc == urlparse(base).netloc

def scrape_emails(base_url: str, max_pages: int = 10) -> list[str]:
    """
    Crawl up to max_pages internal pages (prioritizing contact/about), and collect emails via:
      1) regex on raw HTML
      2) regex on visible text
      3) mailto links, aria-labels, JSON-LD
    """
    visited = {base_url}
    emails = set()

    # 1) Fetch and regex on full raw HTML
    html = fetch_html(base_url)
    emails |= extract_emails_from_text(html)

    # 2) Parse and regex on visible text + soup-based extractors
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text(separator='\n', strip=True)
    emails |= extract_emails_from_text(text)
    emails |= extract_emails_from_soup(soup)

    # 3) Build prioritized crawl list
    links = [
        urljoin(base_url, a['href'])
        for a in soup.find_all('a', href=True)
        if is_internal_link(a['href'], base_url)
    ]
    contact_links = [l for l in links if 'contact' in l.lower() or 'about' in l.lower()]
    other_links   = [l for l in links if l not in contact_links]
    crawl_list    = contact_links + other_links

    # 4) Crawl additional pages
    for link in crawl_list:
        if len(visited) >= max_pages:
            break
        if link in visited:
            continue
        visited.add(link)

        html = fetch_html(link)
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text(separator='\n', strip=True)

        emails |= extract_emails_from_text(html)
        emails |= extract_emails_from_text(text)
        emails |= extract_emails_from_soup(soup)

        time.sleep(0.5)

    return list(emails)
