import os
import time
import json
import subprocess
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

SCENES = {
33: (5, "Character flinches sharply backward as if struck, hand rising defensively in front of the face, eyes widening with hurt, quick sharp motion, dramatic spotlight flickering, dark vignette pulsing slightly, emotional and tense realistic motion."),
54: (10, "Slow dramatic close-up motion: a golden trophy held in the character's hands begins to crack with glowing fracture lines spreading across its surface, then slowly crumbles and dissolves into fine glittering dust falling through the character's fingers, shocked realization expression deepening, dramatic spotlight flickering, cinematic slow motion."),
63: (10, "Wide cinematic slow motion: dark stormy clouds and rough ocean waves gradually calm, the water smoothing out, clouds slowly parting to reveal clear blue sky and soft sunlight breaking through, gentle gull or light particles drifting, character's small silhouette standing still on the shore watching peacefully, serene transformation, smooth realistic motion."),
76: (10, "Character and friend sitting side by side on a bench, both turning slightly to smile warmly at each other, gentle natural laughter motion, soft breeze moving hair and leaves, warm golden-hour light flickering gently, comfortable relaxed realistic motion."),
90: (5, "Character waves goodbye warmly with a gentle smile, soft natural hand motion, gentle blinking, warm golden evening light glowing through the window, calm friendly closing motion."),
}

def main():
    load_env()
    api_key = os.environ.get("KIE_API_KEY")
    img_dir = os.path.join(os.path.dirname(__file__), "images")
    out_dir = os.path.join(os.path.dirname(__file__), "videos")
    os.makedirs(out_dir, exist_ok=True)

    for num in sorted(SCENES.keys()):
        out_path = os.path.join(out_dir, f"scene_{num}.mp4")
        if os.path.exists(out_path):
            print(f"Scene {num}: already exists, skipping")
            continue
        duration, prompt = SCENES[num]
        image_path = os.path.join(img_dir, f"scene_{num}.png")
        try:
            print(f"Scene {num}: uploading image...")
            image_url = upload_image(image_path, api_key)
            print(f"Scene {num}: creating video task (duration={duration})...")
            task_id = create_video_task(image_url, prompt, duration, api_key)
            print(f"Scene {num}: task {task_id}, polling...")
            video_url = poll_task(task_id, api_key)
            download_file(video_url, out_path)
            print(f"Scene {num}: done -> {out_path}")
        except Exception as e:
            print(f"Scene {num}: FAILED - {e}")
        time.sleep(2)

if __name__ == "__main__":
    main()
