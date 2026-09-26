import argparse
import json
from crawler import TiengAnhChoTreEmScraper

def main():
    parser = argparse.ArgumentParser(description="Crawler for tienganhchotreem.com Little Fox resources")
    parser.add_argument("--url", default="https://www.tienganhchotreem.com/my-first-readers-1/", help="Target post URL to crawl")
    parser.add_argument("--download", action="store_true", help="Download the resolved files immediately")
    parser.add_argument("--output-dir", default="downloads", help="Directory to save downloaded files")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode (default: False for anti-bot bypass)")

    args = parser.parse_args()

    scraper = TiengAnhChoTreEmScraper(headless=args.headless, download_dir=args.output_dir)
    result = scraper.crawl_post(args.url, do_download=args.download)

    print("\n================== CRAWL SUMMARY ==================")
    print(f"Title: {result['title']}")
    print(f"Source: {result['url']}")
    for idx, item in enumerate(result.get("results", []), 1):
        print(f"\nItem #{idx}: {item.get('name')}")
        print(f"  Intermediate Link: {item.get('url')}")
        print(f"  Direct Link:       {item.get('direct_link', 'N/A')}")
        if "local_path" in item:
            print(f"  Downloaded Path:   {item.get('local_path')}")

    # Save metadata JSON
    meta_file = "crawl_result.json"
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n[+] Results metadata saved to {meta_file}")

if __name__ == "__main__":
    main()
