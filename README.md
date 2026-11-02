# 💊 IoT-Enabled Smart Pill Inspection and Machine Condition Monitoring System

> Final-year B.Tech project (Project ID **SA47**), Department of Electronics and
> Telecommunication Engineering, Pimpri Chinchwad College of Engineering, Pune,
> Academic Year 2025-26.

![Python](https://img.shields.io/badge/Python-3.x-blue)
![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-green)
![OpenCV](https://img.shields.io/badge/OpenCV-4.x-red)
![Flask](https://img.shields.io/badge/Flask-dashboard-lightgrey)

 Yashraj Pangave 

---

## 🎯 What it does

Pharmaceutical pills coming off a production line can be cracked, discoloured,
or the wrong shape and size, and manual visual inspection is slow and
inconsistent. This project is a working prototype that inspects pills on camera
in real time using a trained YOLOv8 object-detection model and flags each
sampled batch as **GOOD** or **FAIL**.

> **Note:** despite the project title, machine condition monitoring is not
> implemented in this code - this repo contains the vision inspection part.

---

## ⚙️ How it works

- **`main.py`** captures frames from a USB webcam, or from a phone camera using
  DroidCam (USB or WiFi), and runs YOLOv8 inference with the included trained
  weights (`best.pt`). Every 30 frames it saves one batch record to
  `results.json`: the normal and defect counts are summed across those frames,
  and the batch is marked GOOD when at least 75% of the detections are normal
  (configurable in `main.py`). Detections are counted per frame, not tracked
  per pill, so a pill visible in several frames is counted several times.
- **`aapp.py`** is a Flask dashboard that reads `results.json` and serves a live
  view at http://127.0.0.1:5000.
- The project report describes a laptop or a Raspberry Pi 4 as the processing
  unit, with a 12 MP USB webcam or a mobile phone camera for capture.

> ⚠️ This is a student project prototype. It is not a validated or certified
> quality-control system for pharmaceutical manufacturing.

---

## 🚀 Setup

```bash
pip install -r requirements.txt
```

Run the detector (edit the SETTINGS block at the top of `main.py` to match
your camera - USB index, or DroidCam IP/port for WiFi mode):

```bash
python main.py
```

In a second terminal, run the dashboard:

```bash
python aapp.py
```

`results.json` in this repo is supplied sample detector output, so the
dashboard works without a camera connected.

---

## 🙌 Credits

Detection model built on Ultralytics YOLOv8; `best.pt` is the project team's
own fine-tuned weights. Detection, dashboard, and documentation by the SA47
team.
