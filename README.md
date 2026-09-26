# TiengAnhChoTreEm Scraper & Downloader

Công cụ tự động hóa cào dữ liệu và tải tài liệu truyện tranh, audio, PDF từ website [tienganhchotreem.com](https://www.tienganhchotreem.com) (Little Fox series, My First Readers, v.v.).

## Tính năng

- **Bóc tách tự động**: Lấy tiêu đề, mô tả và toàn bộ liên kết tải về của bài viết.
- **Vượt bảo vệ & reCAPTCHA v3**: Tích hợp Playwright với cơ chế mô phỏng hành vi tự nhiên (human-like scrolling/hovering) và cơ chế tự động thử lại (retry) khi gặp hạn chế điểm số của robot.
- **Trích xuất Direct CDN Link**: Tự động giải mã liên kết tải trực tiếp từ CDN server `drive.tienganhchotreem.com`.
- **Tải file tốc độ cao**: Hỗ trợ tải trực tiếp với thanh tiến trình trực quan (MB, %, tốc độ tải).

## Cài đặt

1. Cài đặt các thư viện cần thiết:
```bash
pip install -r requirements.txt
playwright install chromium
```

## Hướng dẫn sử dụng

### 1. Chỉ giải mã và lấy liên kết tải trực tiếp (không tải về ổ cứng)
```bash
python main.py --url https://www.tienganhchotreem.com/my-first-readers-1/
```
Kết quả được xuất ra màn hình và lưu vào tệp `crawl_result.json`.

### 2. Giải mã và tự động tải toàn bộ file (.zip / .pdf / .mp3)
```bash
python main.py --url https://www.tienganhchotreem.com/my-first-readers-1/ --download
```
Các tệp đã tải sẽ được lưu mặc định trong thư mục `./downloads/`.

### 3. Tùy chỉnh thư mục lưu
```bash
python main.py --url https://www.tienganhchotreem.com/my-first-readers-1/ --download --output-dir "D:/LittleFox"
```

## Cấu trúc thư mục

```
Lit/
├── crawler.py          # Module cào chính (Playwright & BeautifulSoup)
├── main.py             # CLI điều khiển
├── requirements.txt    # Danh sách thư viện phụ thuộc
├── .gitignore          # Cấu hình bỏ qua tệp tải về và cache
└── README.md           # Hướng dẫn sử dụng
```
