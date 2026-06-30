import os
import json
import subprocess
import imageio_ffmpeg

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
ROOT = os.path.dirname(__file__)
IMAGES_DIR = os.path.join(ROOT, "images")
VIDEOS_DIR = os.path.join(ROOT, "videos")
SEGMENTS_DIR = os.path.join(ROOT, "segments")
W, H, FPS = 1920, 1080, 24

os.makedirs(SEGMENTS_DIR, exist_ok=True)

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {' '.join(cmd)}\n{r.stderr[-2000:]}")

def make_segment_from_video(video_path, duration, out_path):
    # get source duration
    probe = subprocess.run(
        [FFMPEG, "-i", video_path, "-f", "null", "-"],
        capture_output=True, text=True,
    )
    # crude duration parse not needed; just trim or pad using filters
    cmd = [
        FFMPEG, "-y", "-i", video_path,
        "-vf", f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,fps={FPS}",
        "-t", str(duration),
        "-an",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        out_path,
    ]
    run(cmd)
    # check actual output duration; if shorter than requested, pad by freezing last frame
    out_dur = get_duration(out_path)
    if out_dur < duration - 0.05:
        pad_amount = duration - out_dur
        tmp = out_path + ".tmp.mp4"
        cmd2 = [
            FFMPEG, "-y", "-i", out_path,
            "-vf", f"tpad=stop_mode=clone:stop_duration={pad_amount}",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            tmp,
        ]
        run(cmd2)
        os.replace(tmp, out_path)

def make_segment_from_image(image_path, duration, out_path, zoom_in=True):
    # Ken Burns: slow zoom over the duration
    frames = int(duration * FPS)
    zoom_expr = f"zoom+0.0008" if zoom_in else f"zoom-0.0008"
    cmd = [
        FFMPEG, "-y", "-loop", "1", "-i", image_path,
        "-vf",
        f"scale={W*2}:{H*2}:force_original_aspect_ratio=decrease,"
        f"zoompan=z='{zoom_expr}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps={FPS}",
        "-t", str(duration),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        out_path,
    ]
    run(cmd)

def get_duration(path):
    r = subprocess.run([FFMPEG, "-i", path], capture_output=True, text=True)
    import re
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", r.stderr)
    if not m:
        return 0.0
    h, mi, s = m.groups()
    return int(h) * 3600 + int(mi) * 60 + float(s)

def main():
    with open(os.path.join(ROOT, "scene_timings.json")) as f:
        timings = json.load(f)

    concat_list_path = os.path.join(ROOT, "concat_list.txt")
    with open(concat_list_path, "w") as concat_f:
        for num_str in sorted(timings.keys(), key=lambda x: int(x)):
            num = int(num_str)
            _, _, dur = timings[num_str]
            dur = max(dur, 0.5)
            seg_path = os.path.join(SEGMENTS_DIR, f"seg_{num:03d}.mp4")
            video_path = os.path.join(VIDEOS_DIR, f"scene_{num}.mp4")
            image_path = os.path.join(IMAGES_DIR, f"scene_{num}.png")

            if os.path.exists(seg_path):
                print(f"Scene {num}: segment already exists, skipping")
            elif os.path.exists(video_path):
                print(f"Scene {num}: building from VIDEO (dur={dur:.2f}s)")
                make_segment_from_video(video_path, dur, seg_path)
            else:
                print(f"Scene {num}: building from IMAGE (dur={dur:.2f}s)")
                make_segment_from_image(image_path, dur, seg_path)

            concat_f.write(f"file '{seg_path}'\n")

    print("Concatenating all segments...")
    silent_full = os.path.join(ROOT, "video_no_audio.mp4")
    run([
        FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", concat_list_path,
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        silent_full,
    ])

    print("Adding voice audio...")
    final_out = os.path.join(ROOT, "final_video.mp4")
    voice_path = os.path.join(ROOT, "Nóng giận voice.mp3")
    run([
        FFMPEG, "-y", "-i", silent_full, "-i", voice_path,
        "-c:v", "copy", "-c:a", "aac", "-map", "0:v:0", "-map", "1:a:0",
        "-shortest",
        final_out,
    ])
    print(f"Done: {final_out}")

if __name__ == "__main__":
    main()
