# site_scraper.py
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse


def is_internal_link(href, base_url):
    if not href:
        return False
    parsed      = urlparse(href)
    base_domain = urlparse(base_url).netloc
    return (not parsed.netloc or parsed.netloc == base_domain) and not href.startswith("mailto:")


def scrape_page_content(url):
    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=8)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        text = '\n'.join([line.strip() for line in soup.get_text("\n", strip=True).splitlines() if line.strip()])
        return soup, text
    except Exception:
        return None, ""


def scrape_page_text(url):
    # legacy; uses only text
    _, text = scrape_page_content(url)
    return text


def scrape_site_with_links(base_url, max_pages=5, max_chars=5000):
    visited = set()
    collected = ""

    soup, text = scrape_page_content(base_url)
    if text:
        collected += text + "\n\n"
    visited.add(base_url)

    try:
        internal = []
        if soup:
            for a in soup.find_all('a', href=True):
                link = urljoin(base_url, a['href'])
                if is_internal_link(link, base_url):
                    internal.append(link)
        for link in internal:
            if link not in visited and len(visited) < max_pages:
                _, t = scrape_page_content(link)
                collected += t + "\n\n"
                visited.add(link)
    except Exception as e:
        collected += f"[Error crawling links: {e}]"

    return collected[:max_chars]


def extract_emails_from_text(text: str) -> set[str]:
    pattern = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
    return set(re.findall(pattern, text))


def extract_emails_from_soup(soup) -> set[str]:
    mails = set()
    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.lower().startswith('mailto:'):
            addr = href.split(':',1)[1].split('?')[0]
            mails.add(addr)
    return mails


def scrape_emails(base_url, max_pages=5) -> list[str]:
    visited = set()
    emails  = set()
    queue   = [base_url]

    while queue and len(visited) < max_pages:
        url = queue.pop(0)
        if url in visited:
            continue
        visited.add(url)
        try:
            res = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=8)
            res.raise_for_status()
            soup = BeautifulSoup(res.text, 'html.parser')

            # text-based emails
            text = '\n'.join([line.strip() for line in soup.get_text("\n", strip=True).splitlines() if line.strip()])
            emails.update(extract_emails_from_text(text))

            # mailto: links
            emails.update(extract_emails_from_soup(soup))

            # enqueue internal links
            for a in soup.find_all('a', href=True):
                link = urljoin(base_url, a['href'])
                if is_internal_link(link, base_url) and link not in visited:
                    queue.append(link)
        except Exception:
            pass

    return list(emails)
