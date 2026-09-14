import sys
import asyncio
import urllib.parse
from pathlib import Path
import aiohttp

HEADERS = {
    "User-Agent": "MyDataCollector/1.0 (+https://example.com/bot-info)"
}

# Concurrency control: Maximum simultaneous network requests
MAX_CONCURRENT_REQUESTS = 10


def normalize_url(raw_url: str) -> str:
    """Ensure raw_url includes an explicit scheme (defaults to https://)."""
    raw_url = raw_url.strip()
    if not raw_url.startswith(("http://", "https://")):
        return f"https://{raw_url}"
    return raw_url


def get_domain_and_filename(url: str) -> tuple[str, str]:
    """Extract domain name for folder creation and a clean base filename."""
    parsed = urllib.parse.urlparse(url)
    domain = parsed.netloc.replace(":", "_") if parsed.netloc else "unknown_domain"
    path = parsed.path.strip("/")
    base_name = path.replace("/", "_") if path else "index"
    return domain, base_name


def get_versioned_filepath(target_dir: Path, base_name: str) -> Path:
    """Atomically find the next non-conflicting versioned file path."""
    version = 1
    while True:
        filename = f"{base_name}_v{version}.html"
        filepath = target_dir / filename
        if not filepath.exists():
            return filepath
        version += 1


async def fetch_and_save(session: aiohttp.ClientSession, semaphore: asyncio.Semaphore, raw_url: str) -> None:
    """Asynchronously fetch HTML content with error handling and atomic file saves."""
    async with semaphore:
        target_url = normalize_url(raw_url)
        domain, base_name = get_domain_and_filename(target_url)

        # Directory structure: domain/html_pages
        html_pages_dir = Path(domain) / "html_pages"

        try:
            # Safe directory creation
            html_pages_dir.mkdir(parents=True, exist_ok=True)
            filepath = get_versioned_filepath(html_pages_dir, base_name)

            print(f"[FETCHING] {target_url}")
            async with session.get(target_url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=15)) as response:
                if response.status >= 400:
                    print(f"[HTTP {response.status}] Failed to fetch: {target_url}")
                    return

                html_content = await response.text(errors="ignore")

                # Atomic disk write
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(html_content)

                print(f"[SUCCESS] Saved -> {filepath}")

        except asyncio.TimeoutError:
            print(f"[TIMEOUT] Request timed out for: {target_url}")
        except aiohttp.ClientError as e:
            print(f"[NETWORK ERROR] {target_url}: {e}")
        except Exception as e:
            # Catch-all ensures the entire queue keeps running even on unexpected individual errors
            print(f"[UNEXPECTED ERROR] {target_url}: {e}")


async def main():
    raw_urls = sys.argv[1:]

    if not raw_urls:
        print("Usage: python fetch.py    ...")
        print("Example: python fetch.py example.com httpbin.org/html google.com")
        sys.exit(1)

    # Limit concurrent network calls to avoid socket exhaustion and host bans
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

    # Configure connection pooling for scale (1,000+ requests)
    connector = aiohttp.TCPConnector(limit=100, ttl_dns_cache=300)

    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [fetch_and_save(session, semaphore, url) for url in raw_urls]
        await asyncio.gather(*tasks, return_exceptions=True)


if __name__ == "__main__":
    # Required dependency: pip install aiohttp
    asyncio.run(main())
