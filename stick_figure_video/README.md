# Stick-Figure Video Pipeline — Hướng dẫn chạy trên máy cá nhân

Môi trường cloud (Claude Code on the web) đang chặn kết nối đến `api.kie.ai`
nên các bước gọi API (tạo ảnh, animate video) cần chạy trên máy tính cá nhân
của bạn, nơi không bị chặn mạng.

## 1. Cài đặt

```bash
# Cài Python 3 nếu chưa có (kiểm tra trước)
python3 --version

# Clone repo về máy (thay link nếu khác)
git clone https://github.com/pennynguyen2023-crypto/PENNY-NGUYEN.git
cd PENNY-NGUYEN
git checkout claude/stick-figure-video-clip-6e79ab

# Cài ffmpeg binary qua pip (không cần quyền admin)
pip3 install --user imageio-ffmpeg
python3 -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())"
```

## 2. Tạo file `.env` chứa API key

Tạo file `stick_figure_video/scripts/.env` với nội dung:

```
KIE_API_KEY=<api_key_cua_ban>
```

File này đã được `.gitignore`, sẽ không bị commit lên GitHub.

## 3. Tạo ảnh thử 1 scene đầu để duyệt style

```bash
cd stick_figure_video/scripts
python3 generate_images.py 01 "Minimalist 2D cartoon stick-figure character with a plain round white head, simple black dot eyes, thin curved eyebrows, small expressive mouth, smooth white cylindrical neck and limbs, wearing a plain yellow short-sleeve t-shirt, black trousers, white sneakers. Flat 2D character composited into a highly detailed photorealistic 3D-rendered environment, cinematic lighting, 16:9 widescreen, 1920x1080, high detail, shallow depth of field. Narrator stick-figure stands alone in a dim quiet room at night, looking thoughtful, soft moonlight from a window."
```

Ảnh sẽ lưu ở `stick_figure_video/scripts/images/scene_01.png`. Mở ảnh lên xem
có ưng style không trước khi chạy hàng loạt.

## 4. Chạy hàng loạt 49 scene

Có file `scenes.json` ở `stick_figure_video/scenes.json` chứa toàn bộ 49 scene
đã tách sẵn. Bạn cần viết (hoặc nhờ Claude/Claude Code chạy local viết) một
script nhỏ đọc `scenes.json`, ghép `BASE_STYLE + visual` thành prompt, rồi gọi
`generate_images.py` cho từng scene — bỏ qua scene đã có file ảnh để có thể
resume nếu bị ngắt giữa chừng (xem ví dụ pattern resumable trong
`scripts/generate_images.py`).

Chi phí ước tính: 49 ảnh × ~$0.02 ≈ **$1/video**.

## 5. Animate một số scene bằng Kling (tùy chọn)

Dùng `scripts/upload_file.py` + `scripts/generate_video.py` /
`scripts/batch_generate_videos.py` cho khoảng 5-10 scene có cảm xúc/twist mạnh
nhất (xem gợi ý trong từng scene ở `scenes.json`). Chi phí ~$0.28-0.55/clip.

> Bước giọng đọc + ghép video cuối (FFmpeg) **không cần làm** ở pipeline này
> theo yêu cầu — chỉ dừng lại ở tạo ảnh scene (bước 4) và animate một số scene
> bằng Kling (bước 5).

## Sau khi xong

Commit/push các file kết quả nếu muốn lưu trong repo, hoặc gửi trực tiếp file
video cuối cùng cho người dùng — *không* commit `images/`, `videos/`,
`segments/` vào git (đã có trong `.gitignore`) vì các thư mục này thường rất
nặng.
