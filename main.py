"""
Smart Pill Inspection System
Uses YOLO (best.pt) + DroidCam for real-time pill defect detection.
Writes batch results to results.json for the dashboard (app.py).

DroidCam Setup:
  - USB  : camera index = 0 or 1 (try both)
  - WiFi : set DROIDCAM_IP and DROIDCAM_PORT below
  - Use MODE = "usb" or "wifi" to switch
"""

import sys
import json
import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import cv2
from ultralytics import YOLO

# ──────────────────────────────────────────────────────────────
# SETTINGS — edit these to match your setup
# ──────────────────────────────────────────────────────────────
MODE            = "usb"           # "usb" or "wifi"
USB_INDEX       = 1         # Try 0 if 1 doesn't work
DROIDCAM_IP     = "192.168.1.100"   # Replace with your phone's IP (shown in DroidCam app)
DROIDCAM_PORT   = 4747            # Default DroidCam port
MODEL_PATH      = "best.pt"
CONFIDENCE      = 0.5             # Detection confidence threshold (0.0 – 1.0)
GOOD_THRESHOLD  = 0.75            # ≥75% normal pills → GOOD batch
RESULTS_FILE    = "results.json"  # Dashboard reads this file
BATCH_FRAMES    = 30              # Number of frames that make one "batch"
# ──────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ── Colours (BGR) ─────────────────────────────────────────────
C_WHITE  = (255, 255, 255)
C_NORMAL = (50,  220,  50)
C_DEFECT = (40,   40, 220)
C_INFO   = (220, 220,  60)
C_GOOD   = (0,   230,   0)
C_FAIL   = (0,     0, 230)
C_BLACK  = (0,     0,   0)
FONT     = cv2.FONT_HERSHEY_SIMPLEX

_json_lock = threading.Lock()


# ── Rolling average tracker ────────────────────────────────────
@dataclass
class RollingStats:
    window: int = 30
    _n: list = field(default_factory=list)
    _d: list = field(default_factory=list)

    def update(self, normal: int, defect: int):
        self._n.append(normal)
        self._d.append(defect)
        if len(self._n) > self.window:
            self._n.pop(0)
            self._d.pop(0)

    @property
    def avg_normal(self): return sum(self._n) / len(self._n) if self._n else 0
    @property
    def avg_defect(self): return sum(self._d) / len(self._d) if self._d else 0


# ── Save batch result to JSON ──────────────────────────────────
def save_batch(batch_id: int, normal: int, defect: int):
    total        = normal + defect
    normal_pct   = round((normal / total * 100), 2) if total > 0 else 0
    batch_status = "GOOD" if normal_pct >= GOOD_THRESHOLD * 100 else "FAIL"

    record = {
        "batch_id":    batch_id,
        "timestamp":   datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total":       total,
        "normal":      normal,
        "defect":      defect,
        "normal_pct":  normal_pct,
        "status":      batch_status,
    }

    with _json_lock:
        path = Path(RESULTS_FILE)
        data = []
        if path.exists():
            try:
                data = json.loads(path.read_text())
            except (json.JSONDecodeError, ValueError):
                data = []
        data.append(record)
        path.write_text(json.dumps(data, indent=2))

    log.info("Batch #%d saved — %s | Normal: %d | Defect: %d | %.1f%%",
             batch_id, batch_status, normal, defect, normal_pct)


# ── Text helper (with shadow for readability) ──────────────────
def put_text(frame, text, pos, color, scale=0.7, thickness=2):
    cv2.putText(frame, text, (pos[0]+1, pos[1]+1), FONT, scale, C_BLACK, thickness+1, cv2.LINE_AA)
    cv2.putText(frame, text, pos,                  FONT, scale, color,   thickness,   cv2.LINE_AA)


# ── Draw stats overlay ─────────────────────────────────────────
def draw_overlay(frame, normal: int, defect: int, batch_id: int, frame_in_batch: int):
    total = normal + defect

    panel = frame.copy()
    cv2.rectangle(panel, (10, 10), (310, 230), (15, 15, 15), -1)
    cv2.addWeighted(panel, 0.55, frame, 0.45, 0, frame)

    if total == 0:
        put_text(frame, "No pills detected", (20, 50), C_WHITE, scale=0.65)
        return

    normal_pct   = (normal / total) * 100
    batch_status = "GOOD" if normal_pct >= GOOD_THRESHOLD * 100 else "FAIL"
    status_color = C_GOOD if batch_status == "GOOD" else C_FAIL

    put_text(frame, f"Batch #{batch_id}  [{frame_in_batch}/{BATCH_FRAMES}]", (20, 38), C_INFO,   scale=0.6)
    put_text(frame, f"Total  : {total}",            (20,  68), C_WHITE)
    put_text(frame, f"Normal : {normal}",           (20,  98), C_NORMAL)
    put_text(frame, f"Defect : {defect}",           (20, 128), C_DEFECT)
    put_text(frame, f"Normal%: {normal_pct:.1f}%", (20, 158), C_INFO)
    put_text(frame, f"Batch  : {batch_status}",     (20, 198), status_color, scale=1.0, thickness=3)


def draw_fps(frame, fps: float):
    h = frame.shape[0]
    put_text(frame, f"FPS: {fps:.1f}", (20, h - 15), C_INFO, scale=0.55, thickness=1)


# ── Open DroidCam ──────────────────────────────────────────────
def open_camera() -> cv2.VideoCapture:
    if MODE == "wifi":
        url = f"http://{DROIDCAM_IP}:{DROIDCAM_PORT}/video"
        log.info("Connecting to DroidCam over WiFi: %s", url)
        cap = cv2.VideoCapture(url)
    else:
        log.info("Connecting to DroidCam over USB (index=%d) ...", USB_INDEX)
        cap = cv2.VideoCapture(USB_INDEX)

    if not cap.isOpened():
        if MODE == "wifi":
            log.error("Could not connect. Check IP (%s) and that DroidCam app is open.", DROIDCAM_IP)
        else:
            log.error("Camera index %d not found. Try USB_INDEX = 0", USB_INDEX)
        sys.exit(1)

    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    log.info("DroidCam connected successfully.")
    return cap


# ── Main ───────────────────────────────────────────────────────
def main():
    if not Path(MODEL_PATH).exists():
        log.error("Model not found: %s", MODEL_PATH)
        sys.exit(1)

    log.info("Loading model: %s", MODEL_PATH)
    model       = YOLO(MODEL_PATH)
    class_names = model.names
    log.info("Classes: %s", list(class_names.values()))

    cap       = open_camera()
    stats     = RollingStats(window=BATCH_FRAMES)
    prev_tick = cv2.getTickCount()

    batch_id     = 1
    frame_count  = 0
    batch_normal = 0
    batch_defect = 0

    log.info("Running — press [Q] or [ESC] to quit.")
    log.info("Dashboard: open app.py in another terminal → http://127.0.0.1:5000")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                log.warning("Frame grab failed, retrying ...")
                continue

            results   = model(frame, conf=CONFIDENCE, verbose=False)
            annotated = results[0].plot()
            boxes     = results[0].boxes

            counts = {n: 0 for n in class_names.values()}
            for cls in boxes.cls:
                counts[class_names[int(cls)]] += 1

            normal = counts.get("normal", 0)
            defect = sum(v for k, v in counts.items() if k != "normal")

            batch_normal += normal
            batch_defect += defect
            frame_count  += 1
            stats.update(normal, defect)

            if frame_count >= BATCH_FRAMES:
                save_batch(batch_id, batch_normal, batch_defect)
                batch_id     += 1
                frame_count   = 0
                batch_normal  = 0
                batch_defect  = 0

            draw_overlay(annotated, normal, defect, batch_id, frame_count)

            now       = cv2.getTickCount()
            fps       = cv2.getTickFrequency() / (now - prev_tick)
            prev_tick = now
            draw_fps(annotated, fps)

            cv2.imshow("Pill Inspection System", annotated)
            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), ord("Q"), 27):
                break

    except KeyboardInterrupt:
        log.info("Stopped by user.")
    finally:
        if frame_count > 0:
            save_batch(batch_id, batch_normal, batch_defect)
        cap.release()
        cv2.destroyAllWindows()
        log.info("Session done — avg normal: %.1f | avg defect: %.1f",
                 stats.avg_normal, stats.avg_defect)


if __name__ == "__main__":
    main()
