"""Upload a local file to kie.ai's file storage and get back a public URL.

Required by Kling (and any other model needing an image_url/audio_url input).

IMPORTANT: use curl via subprocess for this multipart upload, not a hand-rolled
urllib/http.client multipart body -- a manually constructed multipart payload
reliably gets rejected with 403 by this endpoint even when headers look
correct. curl -F works first try.
"""
import os
import sys
import json
import subprocess


def upload_file(file_path, api_key, upload_path="uploads", file_name=None):
    file_name = file_name or os.path.basename(file_path)
    out = subprocess.run(
        [
            "curl", "-s", "-X", "POST",
            "https://kieai.redpandaai.co/api/file-stream-upload",
            "-H", f"Authorization: Bearer {api_key}",
            "-F", f"file=@{file_path}",
            "-F", f"uploadPath={upload_path}",
            "-F", f"fileName={file_name}",
        ],
        capture_output=True, text=True, check=True,
    )
    result = json.loads(out.stdout)
    return result["data"]["downloadUrl"]


def load_env(env_path=".env"):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ[k] = v


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python upload_file.py <file_path> [uploadPath]")
        sys.exit(1)
    load_env()
    api_key = os.environ["KIE_API_KEY"]
    upload_path = sys.argv[2] if len(sys.argv) > 2 else "uploads"
    url = upload_file(sys.argv[1], api_key, upload_path)
    print(url)
