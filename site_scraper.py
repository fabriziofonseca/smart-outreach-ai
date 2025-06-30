import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

def is_internal_link(href, base_url):
    if not href:
        return False
    parsed = urlparse(href)
    base_domain = urlparse(base_url).netloc
    return (not parsed.netloc or parsed.netloc == base_domain) and not href.startswith("mailto:")

def scrape_page_text(url):
    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=8)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        for tag in soup(["script", "style", "noscript", "header", "footer", "form", "svg"]):
            tag.decompose()

        lines = [line.strip() for line in soup.get_text("\n", strip=True).splitlines() if line.strip()]
        return "\n".join(lines)

    except Exception as e:
        return f"[Error scraping {url}: {str(e)}]"

def scrape_site_with_links(base_url, max_pages=5, max_chars=5000):
    visited = set()
    collected_text = ""

    homepage_text = scrape_page_text(base_url)
    collected_text += homepage_text + "\n\n"
    visited.add(base_url)

    try:
        res = requests.get(base_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=8)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        links = [urljoin(base_url, a["href"]) for a in soup.find_all("a", href=True)]
        internal_links = [link for link in links if is_internal_link(link, base_url)]

        # Limit to a few pages
        for link in internal_links:
            if link not in visited and len(visited) < max_pages:
                page_text = scrape_page_text(link)
                collected_text += page_text + "\n\n"
                visited.add(link)

    except Exception as e:
        collected_text += f"[Error crawling links: {str(e)}]"

    return collected_text[:max_chars]
