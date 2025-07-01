# site_scraper.py
import re
import time
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup


def fetch_html(url: str) -> str:
    """
    Fetch HTML using requests with broad headers.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    }
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 406:
            # retry with broader Accept
            headers['Accept'] = '*/*'
            res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        return res.text
    except Exception as e:
        print(f"[fetch_html] error {getattr(e, 'response', '')} {e} at {url}")
        return ""


def extract_emails_from_text(text: str) -> set[str]:
    # deobfuscate common patterns
    deobs = text.replace('[at]','@').replace('(at)','@').replace(' at ','@')
    deobs = deobs.replace('[dot]','.').replace('(dot)','.')
    combined = text + '\n' + deobs
    pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    return set(re.findall(pattern, combined, flags=re.IGNORECASE))


def extract_emails_from_soup(soup) -> set[str]:
    mails = set()
    for a in soup.find_all('a', href=True):
        if a['href'].lower().startswith('mailto:'):
            addr = a['href'].split(':',1)[1].split('?')[0]
            mails.add(addr)
    return mails


def is_internal_link(href: str, base: str) -> bool:
    if not href:
        return False
    p = urlparse(href)
    return (not p.netloc or p.netloc == urlparse(base).netloc) and not href.lower().startswith('mailto:')


def scrape_emails(base_url: str, max_pages: int = 10) -> list[str]:
    visited = {base_url}
    emails = set()
    html = fetch_html(base_url)
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text(separator='\n', strip=True)
    emails |= extract_emails_from_text(text)
    emails |= extract_emails_from_soup(soup)

    # priorize contact/about links
    links = [urljoin(base_url, a['href']) for a in soup.find_all('a', href=True) if is_internal_link(a['href'], base_url)]
    contact_links = [l for l in links if 'contact' in l.lower() or 'about' in l.lower()]
    other_links = [l for l in links if l not in contact_links]
    crawl_list = contact_links + other_links

    for link in crawl_list:
        if len(visited) >= max_pages:
            break
        if link in visited:
            continue
        visited.add(link)
        html = fetch_html(link)
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text(separator='\n', strip=True)
        emails |= extract_emails_from_text(text)
        emails |= extract_emails_from_soup(soup)
        time.sleep(0.5)

    return list(emails)
