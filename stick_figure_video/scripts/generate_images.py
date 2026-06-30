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

def api_request(url, method="GET", body=None, api_key=None):
    headers = {"Authorization": f"Bearer {api_key}"}
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())

def create_task(prompt, api_key):
    body = {
        "model": "google/nano-banana",
        "input": {
            "prompt": prompt,
            "output_format": "png",
            "aspect_ratio": "16:9",
        },
    }
    result = api_request("https://api.kie.ai/api/v1/jobs/createTask", "POST", body, api_key)
    return result["data"]["taskId"]

def poll_task(task_id, api_key, timeout=180, interval=5):
    url = f"https://api.kie.ai/api/v1/jobs/recordInfo?taskId={task_id}"
    waited = 0
    while waited < timeout:
        result = api_request(url, "GET", None, api_key)
        data = result["data"]
        state = data.get("state")
        if state == "success":
            result_json = json.loads(data["resultJson"])
            return result_json["resultUrls"][0]
        if state == "fail":
            raise RuntimeError(f"Task failed: {data.get('failMsg')}")
        time.sleep(interval)
        waited += interval
    raise TimeoutError("Task did not complete in time")

def download_image(url, out_path):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp, open(out_path, "wb") as f:
        f.write(resp.read())

def main():
    if len(sys.argv) < 3:
        print("Usage: python generate_image.py <scene_number> <prompt>")
        sys.exit(1)
    scene_num = sys.argv[1]
    prompt = sys.argv[2]

    load_env()
    api_key = os.environ.get("KIE_API_KEY")
    if not api_key:
        print("Missing KIE_API_KEY in .env")
        sys.exit(1)

    print(f"Creating task for scene {scene_num}...")
    task_id = create_task(prompt, api_key)
    print(f"Task ID: {task_id}, polling...")
    image_url = poll_task(task_id, api_key)
    print(f"Image URL: {image_url}")

    out_dir = os.path.join(os.path.dirname(__file__), "images")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"scene_{scene_num}.png")
    download_image(image_url, out_path)
    print(f"Saved to {out_path}")

if __name__ == "__main__":
    main()
