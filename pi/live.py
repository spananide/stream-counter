import os
import sys
import time
import json
import subprocess
import tempfile
import traceback
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import cv2
import numpy as np


def normalize_path(p):
    if os.name == "nt" and len(p) >= 3 and p[0] == "/" and p[2] == "/" and p[1].isalpha():
        return f"{p[1]}:{p[2:]}"
    return p


def get_stream_url(ytdlp, url):
    try:
        cmd = [ytdlp, "-f", "best[height<=480]/worst", "-g", url]
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if p.returncode != 0:
            out = (p.stdout or "") + (p.stderr or "")
            if "offline" in out.lower():
                print("offline")
                return "offline", None
            return "error", None
        lines = [line.strip() for line in (p.stdout or "").splitlines() if line.strip()]
        return ("ok", lines[-1]) if lines else ("error", None)
    except Exception:
        return "error", None


def grab_frame(ffmpeg, url):
    tmp = os.path.join(tempfile.gettempdir(), f"kz_{os.getpid()}_{int(time.time()*1000)}.jpg")
    try:
        cmd = [ffmpeg, "-loglevel", "error", "-y", "-i", url, "-frames:v", "1", "-vf", "scale=852:480", tmp]
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if p.returncode != 0 or not os.path.exists(tmp) or os.path.getsize(tmp) == 0:
            return None
        return cv2.imread(tmp)
    except Exception:
        return None
    finally:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass


def recognize_face(frame, detector, recognizer, names, centroids):
    # returns (letters of everyone in the cam, best sim, face of the main person)
    _, faces = detector.detect(frame)
    seen = []
    if faces is not None:
        for face in faces:
            feat = recognizer.feature(recognizer.alignCrop(frame, face))
            sims = [float(recognizer.match(feat, c, cv2.FaceRecognizerSF_FR_COSINE)) for c in centroids]
            j = int(np.argmax(sims))
            if sims[j] >= 0.45:
                seen.append((float(face[2]), sims[j], str(names[j]), float(face[0] + face[2] / 2), float(face[1] + face[3] / 2), face))
    if not seen:
        return "-", -1.0, None
    main = max(seen, key=lambda x: x[0])
    letters = {main[2]}
    for x in seen:  # 2nd person: similar size, good match, clearly beside the main face
        if x[0] >= 0.6 * main[0] and x[1] >= 0.5 and ((x[3] - main[3]) ** 2 + (x[4] - main[4]) ** 2) ** 0.5 >= 0.9 * main[0]:
            letters.add(x[2])
    return "".join(sorted(letters)), main[1], main[5]


def save_proof_and_sample(repo, frame, person, best_sim, best_face):
    now_berlin = datetime.now(ZoneInfo("Europe/Berlin"))
    day, hh = now_berlin.strftime("%Y-%m-%d"), now_berlin.strftime("%H")
    proof_dir = os.path.join(repo, "proof", day)
    proof_path = os.path.join(proof_dir, f"{hh}.jpg")
    saved_photo = False
    if not os.path.exists(proof_path):
        if person != "-" and best_face is not None:
            fx, fy, fw, fh = best_face[0:4]
            cx, cy = fx + fw / 2.0, fy + fh / 2.0
            nw, nh = fw * 2.2, fh * 2.4
            h, w = frame.shape[:2]
            x1, y1 = max(0, int(round(cx - nw / 2.0))), max(0, int(round(cy - nh / 2.0)))
            x2, y2 = min(w, int(round(cx + nw / 2.0))), min(h, int(round(cy + nh / 2.0)))
            shot = cv2.resize(frame[y1:y2, x1:x2], (186, 160)) if (x2 > x1 and y2 > y1) else frame[0:160, 666:852]
        else:
            shot = frame[0:160, 666:852]
        os.makedirs(proof_dir, exist_ok=True)
        cv2.imwrite(proof_path, shot, [int(cv2.IMWRITE_JPEG_QUALITY), 72])
        saved_photo = True

    samples_path = os.path.join(repo, "samples.jsonl")
    entry = {"t": int(time.time()), "p": person}
    if saved_photo:
        entry["img"] = 1
    with open(samples_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
        f.flush()

    sim_str = f"{best_sim:.4f}" if best_sim >= 0 else "0.0000"
    print(f"{now_berlin.isoformat()} {person} sim={sim_str} photo={1 if saved_photo else 0}", flush=True)
    return saved_photo


def measure(repo, stream_url, ytdlp, ffmpeg, detector, recognizer, names, centroids):
    state, url = get_stream_url(ytdlp, stream_url)
    if state == "offline":
        return "offline"
    if state != "ok" or not url:
        return "error"
    frame = grab_frame(ffmpeg, url)
    if frame is None:
        return "error"
    try:
        person, best_sim, best_face = recognize_face(frame, detector, recognizer, names, centroids)
        save_proof_and_sample(repo, frame, person, best_sim, best_face)
        return "ok"
    finally:
        del frame


def ping_kuma(url):
    if not url:
        return
    sep = "&" if "?" in url else "?"
    try:
        urllib.request.urlopen(f"{url}{sep}status=up&msg=ok", timeout=10)
    except Exception:
        pass


def git_sync(repo):
    try:
        subprocess.run(["git", "add", "samples.jsonl", "proof"], cwd=repo, check=True)
        if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=repo).returncode != 0:
            iso_now = datetime.now(ZoneInfo("Europe/Berlin")).isoformat()
            subprocess.run(["git", "commit", "-m", f"Messung {iso_now}"], cwd=repo, check=True)
        subprocess.run(["git", "pull", "--rebase", "--autostash"], cwd=repo, check=True)
        subprocess.run(["git", "push"], cwd=repo, check=True)
    except Exception as e:
        print(f"git sync error: {e}", file=sys.stderr)
        try:
            subprocess.run(["git", "rebase", "--abort"], cwd=repo, capture_output=True)
        except Exception:
            pass


def main():
    repo = normalize_path(os.environ.get("REPO", str(Path(__file__).resolve().parent.parent)))
    stream_url = os.environ.get("STREAM_URL", "https://www.twitch.tv/nooreax")
    interval = int(os.environ.get("INTERVAL", "300"))
    push_every = int(os.environ.get("PUSH_EVERY", "900"))
    kuma_url = os.environ.get("KUMA_URL", "")
    ytdlp = normalize_path(os.environ.get("YTDLP", "yt-dlp"))
    ffmpeg = normalize_path(os.environ.get("FFMPEG", "ffmpeg"))

    script_dir = Path(__file__).resolve().parent
    yunet_path = str(script_dir / "models" / "yunet.onnx")
    sface_path = str(script_dir / "models" / "sface.onnx")
    cent_data = np.load(str(script_dir / "centroids.npz"))
    names, centroids = cent_data["names"], cent_data["cent"]

    detector = cv2.FaceDetectorYN.create(yunet_path, "", (852, 480), score_threshold=0.85)
    recognizer = cv2.FaceRecognizerSF.create(sface_path, "")

    if "--once" in sys.argv:
        state = measure(repo, stream_url, ytdlp, ffmpeg, detector, recognizer, names, centroids)
        sys.exit(0 if state in ("ok", "offline") else 1)

    last_push = 0.0
    while True:
        try:
            now = time.time()
            if last_push == 0.0 or (now - last_push >= push_every):
                git_sync(repo)
                last_push = time.time()
            state = measure(repo, stream_url, ytdlp, ffmpeg, detector, recognizer, names, centroids)
            if state in ("ok", "offline") and kuma_url:
                ping_kuma(kuma_url)
            if time.time() - last_push >= push_every:
                git_sync(repo)
                last_push = time.time()
        except Exception:
            traceback.print_exc()

        now = time.time()
        sleep_sec = interval - (now % interval)
        if sleep_sec < 0.5:
            sleep_sec += interval
        time.sleep(sleep_sec)


if __name__ == "__main__":
    main()
