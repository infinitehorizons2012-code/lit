"""
Downloader for Video and Quiz from tienganhchotreem.com
Supports:
- Extracting full playlist of stories (HLS m3u8 streams)
- Downloading high quality MP4 videos with yt-dlp
- Downloading VTT subtitles and thumbnails
- Fetching full quiz questions, answer choices & audio from API
- Slicing quiz sprite images (for image-based quizzes)
- Generating an offline interactive quiz HTML player
"""

import os
import re
import sys
import json
import time
import subprocess
import urllib.request
import urllib.parse
from io import BytesIO
from typing import Dict, List, Optional
from PIL import Image

QUIZ_API_URL = "https://www.tienganhchotreem.com/tools/apiquizlf.php"
QUIZ_MEDIA_BASE = "https://media.tienganhchotreem.com/lf/quiz/"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def sanitize_filename(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "_", name).strip()

class VideoQuizCrawler:
    def __init__(self, output_dir: str = "downloads"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def fetch_playlist(self, post_url: str) -> List[Dict]:
        """Fetch the playlist of all stories/episodes embedded on the page."""
        print(f"[*] Fetching page: {post_url}")
        req = urllib.request.Request(post_url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req) as resp:
            html = resp.read().decode("utf-8", errors="ignore")

        match = re.search(r'const\s+playlistData\s*=\s*(\[.*?\]);', html, re.DOTALL)
        if not match:
            raise ValueError("Could not find playlistData in page HTML.")

        playlist = json.loads(match.group(1))
        print(f"[+] Found {len(playlist)} episode(s) in playlist.")
        return playlist

    def download_video(self, item: Dict, dest_dir: str) -> str:
        """Download m3u8 stream as MP4 using yt-dlp."""
        title = item.get("title", "video")
        stream_url = item.get("file")
        out_mp4 = os.path.join(dest_dir, f"{sanitize_filename(title)}.mp4")

        if os.path.exists(out_mp4) and os.path.getsize(out_mp4) > 1024 * 1024:
            print(f"    [SKIP] Video already exists: {out_mp4}")
            return out_mp4

        print(f"    [*] Downloading video via yt-dlp -> {os.path.basename(out_mp4)}...")
        cmd = [
            "yt-dlp",
            "--add-header", "Referer:https://www.tienganhchotreem.com/",
            "--add-header", f"User-Agent:{USER_AGENT}",
            stream_url,
            "-o", out_mp4,
            "--no-playlist",
            "--quiet",
            "--progress"
        ]
        res = subprocess.run(cmd)
        if res.returncode != 0:
            print(f"    [-] yt-dlp error, retrying without quiet...")
            subprocess.run(cmd[:-2])

        # Download subtitle track if available
        tracks = item.get("tracks", [])
        for t in tracks:
            vtt_url = t.get("file")
            if vtt_url:
                vtt_name = f"{sanitize_filename(title)}.vtt"
                vtt_dest = os.path.join(dest_dir, vtt_name)
                try:
                    self._download_direct_file(vtt_url, vtt_dest)
                    print(f"    [+] Subtitle downloaded: {vtt_name}")
                except Exception as e:
                    print(f"    [-] Failed downloading subtitle: {e}")

        # Download thumbnail image if available
        img_url = item.get("image")
        if img_url:
            img_dest = os.path.join(dest_dir, "thumbnail.jpg")
            try:
                self._download_direct_file(img_url, img_dest)
            except Exception:
                pass

        return out_mp4

    def fetch_quiz_data(self, video_id: str) -> Optional[Dict]:
        """Fetch quiz questions and metadata from api.php."""
        data = urllib.parse.urlencode({"id": video_id}).encode("utf-8")
        req = urllib.request.Request(
            QUIZ_API_URL,
            data=data,
            headers={
                "User-Agent": USER_AGENT,
                "Content-Type": "application/x-www-form-urlencoded"
            }
        )
        try:
            with urllib.request.urlopen(req) as resp:
                res = resp.read().decode("utf-8", errors="ignore")
                return json.loads(res)
        except Exception as e:
            print(f"    [-] Error fetching quiz data for {video_id}: {e}")
            return None

    def download_quiz(self, video_id: str, title: str, dest_dir: str) -> Optional[Dict]:
        """Download quiz JSON, audio files, slice sprite images, and create offline player."""
        quiz_data = self.fetch_quiz_data(video_id)
        if not quiz_data or not quiz_data.get("question"):
            print(f"    [-] No quiz available for {video_id}")
            return None

        quiz_dir = os.path.join(dest_dir, "quiz")
        os.makedirs(quiz_dir, exist_ok=True)

        # Save raw quiz JSON
        quiz_json_path = os.path.join(quiz_dir, "quiz.json")
        with open(quiz_json_path, "w", encoding="utf-8") as f:
            json.dump(quiz_data, f, ensure_ascii=False, indent=2)

        # Download question audio files
        audio_dir = os.path.join(quiz_dir, "audio")
        os.makedirs(audio_dir, exist_ok=True)
        questions = quiz_data.get("question", [])

        print(f"    [*] Downloading {len(questions)} quiz audio clip(s)...")
        for q in questions:
            sound_rel = q.get("sound_url")
            if sound_rel:
                sound_url = QUIZ_MEDIA_BASE + sound_rel
                local_audio_name = f"q_{q.get('no', 1)}.mp3"
                local_audio_path = os.path.join(audio_dir, local_audio_name)
                try:
                    self._download_direct_file(sound_url, local_audio_path)
                    q["local_audio"] = f"audio/{local_audio_name}"
                except Exception as e:
                    print(f"    [-] Could not download audio {sound_url}: {e}")

        # Download sound effects (correct/incorrect)
        try:
            self._download_direct_file(QUIZ_MEDIA_BASE + "quiz_correct.mp3", os.path.join(audio_dir, "quiz_correct.mp3"))
            self._download_direct_file(QUIZ_MEDIA_BASE + "quiz_incorrect.mp3", os.path.join(audio_dir, "quiz_incorrect.mp3"))
        except Exception:
            pass

        # Handle images for type 'N' (Image selection)
        quiz_type = quiz_data.get("type")
        if quiz_type == "N":
            img_dir = os.path.join(quiz_dir, "images")
            os.makedirs(img_dir, exist_ok=True)
            sprite_url = f"{QUIZ_MEDIA_BASE}{video_id}/quiz_merge.png"
            sprite_path = os.path.join(quiz_dir, "quiz_merge.png")

            try:
                print("    [*] Downloading and slicing quiz images...")
                self._download_direct_file(sprite_url, sprite_path)
                with Image.open(sprite_path) as img:
                    num_frames = len(questions)
                    frame_h = img.height // num_frames
                    for idx, q in enumerate(questions, 1):
                        crop = img.crop((0, (idx - 1) * frame_h, img.width, idx * frame_h))
                        crop_name = f"question_{idx}.png"
                        crop.save(os.path.join(img_dir, crop_name))
                        q["local_image"] = f"images/{crop_name}"
            except Exception as e:
                print(f"    [-] Error slicing sprite image: {e}")

        # Generate offline interactive HTML quiz player
        self._generate_offline_quiz_html(quiz_data, title, quiz_dir)
        print(f"    [+] Quiz packaged successfully: {quiz_dir}")
        return quiz_data

    def _generate_offline_quiz_html(self, quiz_data: Dict, title: str, quiz_dir: str):
        """Build a standalone, offline interactive quiz web page for the child to practice."""
        html_content = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Quiz: {title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
            background: #f0f4f8;
            margin: 0;
            padding: 20px;
            display: flex;
            justify-content: center;
        }}
        .quiz-card {{
            background: white;
            max-width: 650px;
            width: 100%;
            border-radius: 16px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.08);
            overflow: hidden;
            padding: 24px;
        }}
        h2 {{
            margin-top: 0;
            color: #1e3a8a;
            text-align: center;
        }}
        .progress {{
            font-weight: 600;
            color: #64748b;
            margin-bottom: 16px;
            text-align: center;
        }}
        .question-box {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
            background: #eff6ff;
            padding: 16px;
            border-radius: 12px;
            margin-bottom: 24px;
        }}
        .question-text {{
            font-size: 1.25rem;
            color: #1e293b;
            font-weight: 500;
        }}
        .speaker-btn {{
            background: #3b82f6;
            color: white;
            border: none;
            border-radius: 50%;
            width: 44px;
            height: 44px;
            font-size: 20px;
            cursor: pointer;
            transition: transform 0.1s;
        }}
        .speaker-btn:active {{
            transform: scale(0.95);
        }}
        .options-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
        }}
        .option-img-card {{
            border: 4px solid #e2e8f0;
            border-radius: 12px;
            cursor: pointer;
            overflow: hidden;
            transition: all 0.2s;
            background: #fff;
        }}
        .option-img-card:hover {{
            border-color: #93c5fd;
            transform: translateY(-2px);
        }}
        .option-img-card img {{
            width: 100%;
            display: block;
        }}
        .option-img-card.correct {{
            border-color: #22c55e !important;
            box-shadow: 0 0 0 4px rgba(34, 197, 94, 0.3);
        }}
        .option-img-card.incorrect {{
            border-color: #ef4444 !important;
            opacity: 0.6;
        }}
        .actions {{
            margin-top: 24px;
            text-align: center;
        }}
        .btn-next {{
            background: #22c55e;
            color: white;
            font-size: 1.1rem;
            font-weight: bold;
            padding: 12px 32px;
            border: none;
            border-radius: 30px;
            cursor: pointer;
            display: none;
        }}
        .btn-next:hover {{
            background: #16a34a;
        }}
        .score-box {{
            text-align: center;
            padding: 30px;
        }}
        .score-box h3 {{
            font-size: 2rem;
            color: #1e3a8a;
            margin-bottom: 8px;
        }}
    </style>
</head>
<body>
    <div class="quiz-card" id="quiz-card">
        <h2>{title}</h2>
        <div class="progress" id="progress">Đang tải...</div>
        <div class="question-box">
            <span class="question-text" id="q-text">...</span>
            <button class="speaker-btn" id="audio-btn" onclick="playCurrentAudio()">🔊</button>
        </div>
        <div class="options-grid" id="options-container"></div>
        <div class="actions">
            <button class="btn-next" id="btn-next" onclick="nextQuestion()">Tiếp tục ➔</button>
        </div>
    </div>

    <script>
        const quizData = {json.dumps(quiz_data, ensure_ascii=False)};
        let currentIdx = 0;
        let score = 0;
        let audioPlayer = new Audio();
        let fxPlayer = new Audio();

        function shuffle(arr) {{
            return [...arr].sort(() => Math.random() - 0.5);
        }}

        function loadQuestion() {{
            const q = quizData.question[currentIdx];
            document.getElementById('progress').innerText = `Câu ${{currentIdx + 1}} / ${{quizData.question.length}}`;
            document.getElementById('q-text').innerText = quizData.type === 'N' ? "Nghe và chọn bức tranh đúng." : q.text;
            document.getElementById('btn-next').style.display = 'none';

            playCurrentAudio();

            const container = document.getElementById('options-container');
            container.innerHTML = '';

            if (quizData.type === 'N') {{
                // Pick 1 wrong answer randomly
                const wrongChoices = quizData.question.filter(item => item.no !== q.no);
                const randomWrong = wrongChoices[Math.floor(Math.random() * wrongChoices.length)];
                const options = shuffle([q, randomWrong]);

                options.forEach(opt => {{
                    const card = document.createElement('div');
                    card.className = 'option-img-card';
                    card.innerHTML = `<img src="${{opt.local_image}}" alt="Option">`;
                    card.onclick = () => checkImageAnswer(opt.no === q.no, card, q.no);
                    card.dataset.no = opt.no;
                    container.appendChild(card);
                }});
            }}
        }}

        function playCurrentAudio() {{
            const q = quizData.question[currentIdx];
            if (q.local_audio) {{
                audioPlayer.src = q.local_audio;
                audioPlayer.play().catch(e => console.log(e));
            }}
        }}

        function checkImageAnswer(isCorrect, cardEl, correctNo) {{
            document.querySelectorAll('.option-img-card').forEach(el => el.onclick = null);
            if (isCorrect) {{
                score++;
                cardEl.classList.add('correct');
                fxPlayer.src = 'audio/quiz_correct.mp3';
            }} else {{
                cardEl.classList.add('incorrect');
                document.querySelectorAll('.option-img-card').forEach(el => {{
                    if (parseInt(el.dataset.no) === correctNo) el.classList.add('correct');
                }});
                fxPlayer.src = 'audio/quiz_incorrect.mp3';
            }}
            fxPlayer.play().catch(() => {{}});
            document.getElementById('btn-next').style.display = 'inline-block';
        }}

        function nextQuestion() {{
            currentIdx++;
            if (currentIdx < quizData.question.length) {{
                loadQuestion();
            }} else {{
                document.getElementById('quiz-card').innerHTML = `
                    <div class="score-box">
                        <h3>Hoàn thành bài tập! 🎉</h3>
                        <p style="font-size: 1.3rem;">Bé đã trả lời đúng <strong>${{score}} / ${{quizData.question.length}}</strong> câu.</p>
                        <button class="btn-next" style="display:inline-block; margin-top:20px;" onclick="location.reload()">Làm lại bài</button>
                    </div>
                `;
            }}
        }}

        loadQuestion();
    </script>
</body>
</html>
"""
        with open(os.path.join(quiz_dir, "quiz_interactive.html"), "w", encoding="utf-8") as f:
            f.write(html_content)

    def _download_direct_file(self, url: str, dest_path: str):
        """Helper to download a direct file with progress."""
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req) as resp, open(dest_path, "wb") as f:
            while True:
                chunk = resp.read(1024 * 32)
                if not chunk:
                    break
                f.write(chunk)

    def crawl(self, post_url: str, selected_indices: Optional[List[int]] = None, video_only: bool = False, quiz_only: bool = False):
        """Main crawl flow for videos and quizzes."""
        playlist = self.fetch_playlist(post_url)

        if selected_indices is None:
            items_to_process = list(enumerate(playlist, 1))
        else:
            items_to_process = [(idx, playlist[idx - 1]) for idx in selected_indices if 1 <= idx <= len(playlist)]

        print(f"\n[+] Total items to download: {len(items_to_process)}")

        for order, item in items_to_process:
            title = item.get("title", f"Episode_{order}")
            video_id = item.get("id", f"ID_{order}")
            folder_name = f"{order:02d}_{sanitize_filename(title)}"
            episode_dir = os.path.join(self.output_dir, folder_name)
            os.makedirs(episode_dir, exist_ok=True)

            print(f"\n========================================================")
            print(f"[{order}/{len(playlist)}] Processing: {title} (ID: {video_id})")
            print(f"========================================================")

            if not quiz_only:
                self.download_video(item, episode_dir)

            if not video_only:
                self.download_quiz(video_id, title, episode_dir)

        print("\n[OK] ALL DOWNLOADS FINISHED SUCCESSFULLY!")
