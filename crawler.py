"""
Core scraper module for tienganhchotreem.com
"""

import os
import re
import sys
import time
import urllib.request
import urllib.parse
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

class TiengAnhChoTreEmScraper:
    def __init__(self, headless: bool = False, download_dir: str = "downloads"):
        self.headless = headless
        self.download_dir = download_dir
        os.makedirs(self.download_dir, exist_ok=True)

    def extract_post_info(self, post_url: str) -> Dict:
        """Fetch article title, description, and intermediate download links."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        req = urllib.request.Request(post_url, headers=headers)
        with urllib.request.urlopen(req) as resp:
            html = resp.read().decode("utf-8", errors="ignore")

        soup = BeautifulSoup(html, "html.parser")
        
        # Get title
        title_el = soup.find("h1", class_="title") or soup.find("h1")
        title = title_el.get_text(strip=True) if title_el else "Unknown Title"
        
        # Get description
        content_el = soup.find("div", class_="thecontent") or soup.find("div", class_="entry-content")
        desc = ""
        if content_el:
            p_tags = content_el.find_all("p")
            if p_tags:
                desc = p_tags[0].get_text(strip=True)

        # Find download links
        download_links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            text = a.get_text(strip=True)
            if "hoc-tieng-anh-theo-phuong-phap-dam-chim-immersion-tai-nha/?data=" in href:
                download_links.append({
                    "name": text or "Tải về",
                    "url": href
                })
        
        return {
            "title": title,
            "description": desc,
            "url": post_url,
            "download_links": download_links
        }

    def resolve_direct_link(self, intermediate_url: str, page, max_retries: int = 3) -> Optional[str]:
        """Use Playwright to bypass reCAPTCHA v3 and obtain the real CDN direct download link."""
        for attempt in range(1, max_retries + 1):
            print(f"[*] Navigating to verification page (attempt {attempt}/{max_retries})...")
            page.goto(intermediate_url, wait_until="networkidle")
            time.sleep(3)

            button = page.locator("#download-button")
            if not button.is_visible():
                print("[-] Button #download-button not found!")
                return None

            # Simulate human behavior: scroll down a bit, hover over the button
            try:
                page.mouse.wheel(0, 300)
                time.sleep(1)
                button.hover()
                time.sleep(2)
            except Exception:
                pass

            print("[*] Clicking download verification button...")
            try:
                button.click()
            except Exception as e:
                print(f"[-] Click error: {e}")

            # Wait for the result link to appear
            link_selector = "a[href*='drive.tienganhchotreem.com']"
            for _ in range(12):
                time.sleep(1)
                if page.locator(link_selector).count() > 0:
                    direct_link = page.locator(link_selector).first.get_attribute("href")
                    if direct_link:
                        return direct_link.replace("&amp;", "&")
                
                content = page.content()
                match = re.search(r'href=[\"\'](https://drive\.tienganhchotreem\.com/download\.php\?[^\"\']+)[\"\']', content)
                if match:
                    return match.group(1).replace("&amp;", "&")
                
                if "Xác minh không thành công" in content:
                    print("[-] reCAPTCHA scored low on this attempt. Waiting before retry...")
                    time.sleep(3)
                    break

        print("[-] Failed to retrieve direct link after maximum retries.")
        return None

    def download_file(self, direct_url: str, filename: Optional[str] = None) -> str:
        """Download file with progress report."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        req = urllib.request.Request(direct_url, headers=headers)
        
        with urllib.request.urlopen(req) as resp:
            # Determine filename
            if not filename:
                cd = resp.headers.get("Content-Disposition", "")
                if "filename=" in cd:
                    fname_match = re.search(r'filename=[\"\']?([^\"\';]+)[\"\']?', cd)
                    if fname_match:
                        filename = fname_match.group(1)
            
            if not filename:
                parsed = urllib.parse.urlparse(direct_url)
                params = urllib.parse.parse_qs(parsed.query)
                if "file" in params:
                    filename = os.path.basename(params["file"][0])
                else:
                    filename = f"file_{int(time.time())}.zip"

            dest_path = os.path.join(self.download_dir, filename)
            total_size = int(resp.headers.get("Content-Length", 0))

            print(f"[+] Downloading: {filename} ({total_size / (1024*1024):.2f} MB)")
            
            downloaded = 0
            start_time = time.time()
            with open(dest_path, "wb") as f:
                while True:
                    chunk = resp.read(1024 * 64)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    elapsed = time.time() - start_time
                    speed = (downloaded / (1024 * 1024)) / elapsed if elapsed > 0 else 0
                    percent = (downloaded / total_size * 100) if total_size > 0 else 0
                    sys.stdout.write(f"\r    {downloaded / (1024*1024):.2f} MB / {total_size / (1024*1024):.2f} MB [{percent:.1f}%] - {speed:.2f} MB/s")
                    sys.stdout.flush()

            print(f"\n[+] Saved to: {dest_path}")
            return dest_path

    def crawl_post(self, post_url: str, do_download: bool = True) -> Dict:
        """Complete workflow: extract info, resolve links, download files."""
        print(f"==================================================")
        print(f"Crawling: {post_url}")
        print(f"==================================================")
        info = self.extract_post_info(post_url)
        print(f"Title: {info['title']}")
        print(f"Found {len(info['download_links'])} download link(s)")

        resolved_items = []
        with sync_playwright() as p:
            # Use Chrome channel to guarantee clean browser fingerprint
            browser = p.chromium.launch(
                headless=self.headless,
                channel="chrome",
                args=["--disable-blink-features=AutomationControlled"]
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")

            for item in info["download_links"]:
                name = item["name"]
                inter_url = item["url"]
                print(f"\n--- Resolving link for: {name} ---")
                direct_link = self.resolve_direct_link(inter_url, page)
                if direct_link:
                    print(f"[OK] Direct link: {direct_link}")
                    item["direct_link"] = direct_link
                    if do_download:
                        saved_path = self.download_file(direct_link)
                        item["local_path"] = saved_path
                else:
                    print(f"[FAIL] Could not resolve direct link for {name}")
                resolved_items.append(item)

            browser.close()

        info["results"] = resolved_items
        return info
