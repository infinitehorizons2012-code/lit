import argparse
import json
import sys
from crawler import TiengAnhChoTreEmScraper
from video_quiz_crawler import VideoQuizCrawler

def parse_episodes(ep_str: str):
    if not ep_str:
        return None
    res = set()
    parts = ep_str.split(",")
    for p in parts:
        p = p.strip()
        if "-" in p:
            start, end = p.split("-")
            for i in range(int(start), int(end) + 1):
                res.add(i)
        elif p.isdigit():
            res.add(int(p))
    return sorted(list(res))

def main():
    parser = argparse.ArgumentParser(description="Downloader for tienganhchotreem.com (Videos, Quizzes & Documents)")
    parser.add_argument("--url", default="https://www.tienganhchotreem.com/my-first-readers-1/", help="Target post URL to crawl")
    parser.add_argument("--list", action="store_true", help="List all video/quiz episodes in this series")
    parser.add_argument("--episodes", default="1", help="Select episode index to download, e.g. '1', '1,2,3', '1-5', or 'all'")
    parser.add_argument("--video-only", action="store_true", help="Download only videos and subtitles")
    parser.add_argument("--quiz-only", action="store_true", help="Download only quizzes (questions, images, audio, offline HTML)")
    parser.add_argument("--output-dir", default="downloads", help="Directory to save downloaded files")
    parser.add_argument("--download-doc", action="store_true", help="Download the legacy PDF/MP3 zip archives instead")

    args = parser.parse_args()

    # Legacy PDF/MP3 download mode
    if args.download_doc:
        print("[*] Running in Document (PDF/MP3) download mode...")
        scraper = TiengAnhChoTreEmScraper(download_dir=args.output_dir)
        scraper.crawl_post(args.url, do_download=True)
        return

    # Video & Quiz mode
    crawler = VideoQuizCrawler(output_dir=args.output_dir)
    playlist = crawler.fetch_playlist(args.url)

    if args.list:
        print("\n================== EPISODE PLAYLIST ==================")
        for idx, item in enumerate(playlist, 1):
            print(f"[{idx:02d}] {item.get('title')} (ID: {item.get('id')})")
        print("======================================================")
        return

    selected_indices = None
    if args.episodes.lower() != "all":
        selected_indices = parse_episodes(args.episodes)

    crawler.crawl(
        args.url,
        selected_indices=selected_indices,
        video_only=args.video_only,
        quiz_only=args.quiz_only
    )

if __name__ == "__main__":
    main()
