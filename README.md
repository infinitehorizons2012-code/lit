# TiengAnhChoTreEm Scraper & Downloader (Little Fox Series)

Bộ công cụ tự động hóa cào dữ liệu và tải trọn gói: **Video HD (.mp4)**, **Phụ đề (.vtt)** và **Quiz bài tập tương tác** từ trang [tienganhchotreem.com](https://www.tienganhchotreem.com) (Little Fox series, My First Readers 1, v.v.).

---

## 🌟 Tính năng nổi bật

1. **Tải Video & Phụ đề**:
   - Trích xuất luồng m3u8 và tải thành tệp MP4 chất lượng cao thông qua `yt-dlp`.
   - Tải kèm file phụ đề tiếng Anh (`.vtt`) và ảnh đại diện thumbnail (`.jpg`).
2. **Tải trọn bộ Quiz bài tập (Đúng như trên web)**:
   - Gọi trực tiếp API nội bộ để lấy danh sách câu hỏi, đáp án, câu mẫu.
   - Tải file âm thanh câu hỏi (`.mp3`) và hiệu ứng âm thanh trả lời đúng/sai (`quiz_correct.mp3`, `quiz_incorrect.mp3`).
   - Tự động tải ảnh sprite ghép và **cắt nhỏ thành từng bức tranh tương ứng cho từng câu hỏi** (như dạng *"Nghe và chọn bức tranh đúng"*).
   - **Tự động đóng gói giao diện làm bài tập offline (`quiz_interactive.html`)**: Cho phép bé mở trực tiếp trên máy tính để bấm loa nghe và chọn đáp án tương tác mà không cần internet!
3. **Quản lý danh sách tập linh hoạt**:
   - Liệt kê toàn bộ danh sách tập trong series (ví dụ My First Readers 1 có 64 tập).
   - Tải theo tập chỉ định (`--episodes 1`, `--episodes 1,2,3`, `--episodes 1-10`) hoặc tải toàn bộ (`--episodes all`).
   - Tùy chọn chỉ tải Video (`--video-only`) hoặc chỉ tải Quiz (`--quiz-only`).

---

## ⚙️ Cài đặt

```bash
pip install -r requirements.txt
```

*(Lưu ý: Công cụ sử dụng `yt-dlp` và `ffmpeg` để tải video).*

---

## 🚀 Hướng dẫn sử dụng

### 1. Xem danh sách toàn bộ các tập trong series
```bash
python main.py --list
```
Ví dụ xuất ra:
```
[01] I See (ID: C0000537)
[02] Happy Birthday (ID: C0000545)
...
[64] Merry Christmas! (ID: C0000557)
```

### 2. Tải Video và Quiz của 1 tập cụ thể (ví dụ tập 1 "I See")
```bash
python main.py --episodes 1
```

### 3. Tải nhiều tập cùng lúc (ví dụ từ tập 1 đến tập 5)
```bash
python main.py --episodes 1-5
```

### 4. Tải toàn bộ tất cả 64 tập
```bash
python main.py --episodes all
```

### 5. Chỉ tải Quiz (Không tải Video)
Nếu chỉ cần bộ câu hỏi, âm thanh, hình ảnh và trang làm bài tương tác:
```bash
python main.py --episodes 1-10 --quiz-only
```

### 6. Chỉ tải Video & Phụ đề (Không tải Quiz)
```bash
python main.py --episodes 1-10 --video-only
```

---

## 📁 Cấu trúc thư mục tải về

Mỗi tập truyện sẽ được tự động đóng gói gọn gàng:
```
downloads/
└── 01_I See/
    ├── I See.mp4                 # Video hoạt hình HD
    ├── I See.vtt                 # Phụ đề tiếng Anh
    ├── thumbnail.jpg             # Ảnh bìa
    └── quiz/                     # Trọn gói bài tập trắc nghiệm
        ├── quiz_interactive.html # Trang web làm bài tập tương tác Offline
        ├── quiz.json             # Dữ liệu câu hỏi & đáp án dạng JSON
        ├── audio/                # Toàn bộ âm thanh câu hỏi & hiệu ứng âm thanh
        │   ├── q_1.mp3
        │   ├── q_2.mp3
        │   ├── quiz_correct.mp3
        │   └── quiz_incorrect.mp3
        └── images/               # Từng bức tranh tương ứng cắt từ sprite sheet
            ├── question_1.png
            ├── question_2.png
            └── ...
```
Chỉ cần nhấp đúp vào file `quiz_interactive.html`, bé có thể bấm loa nghe giọng đọc bản xứ và click chọn bức tranh đúng y hệt giao diện trên web.
