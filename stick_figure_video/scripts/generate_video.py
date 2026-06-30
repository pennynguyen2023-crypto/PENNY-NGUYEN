import os
import sys
import time
import json
import urllib.request

def load_env():
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ[k] = v

def api_request_json(url, method="GET", body=None, api_key=None):
    headers = {"Authorization": f"Bearer {api_key}"}
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())

def upload_image(file_path, api_key):
    import subprocess
    file_name = os.path.basename(file_path)
    out = subprocess.run(
        [
            "curl", "-s", "-X", "POST",
            "https://kieai.redpandaai.co/api/file-stream-upload",
            "-H", f"Authorization: Bearer {api_key}",
            "-F", f"file=@{file_path}",
            "-F", "uploadPath=images/user-uploads",
            "-F", f"fileName={file_name}",
        ],
        capture_output=True, text=True, check=True,
    )
    result = json.loads(out.stdout)
    return result["data"]["downloadUrl"]

def create_video_task(image_url, prompt, duration, api_key, sound=False):
    body = {
        "model": "kling-2.6/image-to-video",
        "input": {
            "prompt": prompt,
            "image_urls": [image_url],
            "sound": sound,
            "duration": str(duration),
        },
    }
    result = api_request_json("https://api.kie.ai/api/v1/jobs/createTask", "POST", body, api_key)
    return result["data"]["taskId"]

def poll_task(task_id, api_key, timeout=600, interval=10):
    url = f"https://api.kie.ai/api/v1/jobs/recordInfo?taskId={task_id}"
    waited = 0
    while waited < timeout:
        result = api_request_json(url, "GET", None, api_key)
        data = result["data"]
        state = data.get("state")
        if state == "success":
            return json.loads(data["resultJson"])["resultUrls"][0]
        if state == "fail":
            raise RuntimeError(f"Task failed: {data.get('failMsg')}")
        time.sleep(interval)
        waited += interval
    raise TimeoutError("Task did not complete in time")

def download_file(url, out_path):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp, open(out_path, "wb") as f:
        f.write(resp.read())

def main():
    if len(sys.argv) < 4:
        print("Usage: python generate_video.py <scene_number> <duration:5|10> <prompt>")
        sys.exit(1)
    scene_num = sys.argv[1]
    duration = sys.argv[2]
    prompt = sys.argv[3]

    load_env()
    api_key = os.environ.get("KIE_API_KEY")

    image_path = os.path.join(os.path.dirname(__file__), "images", f"scene_{scene_num}.png")
    print(f"Uploading image for scene {scene_num}...")
    image_url = upload_image(image_path, api_key)
    print(f"Uploaded: {image_url}")

    print(f"Creating video task...")
    task_id = create_video_task(image_url, prompt, duration, api_key)
    print(f"Task ID: {task_id}, polling (this can take a few minutes)...")
    video_url = poll_task(task_id, api_key)
    print(f"Video URL: {video_url}")

    out_dir = os.path.join(os.path.dirname(__file__), "videos")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"scene_{scene_num}.mp4")
    download_file(video_url, out_path)
    print(f"Saved to {out_path}")

if __name__ == "__main__":
    main()
