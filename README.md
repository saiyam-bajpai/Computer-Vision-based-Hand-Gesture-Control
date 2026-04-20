# 🖐️ GestureFlow v6.0: Neural Gesture Interface
### *A B.Tech CSD (Computer Science & Design) Micro Project — Human-Computer Interaction*

![Python](https://img.shields.io/badge/Made%20with-Python-blue?style=for-the-badge&logo=python)
![MediaPipe](https://img.shields.io/badge/AI-MediaPipe-brightgreen?style=for-the-badge)
![Flask](https://img.shields.io/badge/Framework-Flask-lightgrey?style=for-the-badge&logo=flask)
![OpenCV](https://img.shields.io/badge/Vision-OpenCV-red?style=for-the-badge&logo=opencv)
![Status](https://img.shields.io/badge/Status-Version_6.0_Spatial-blueviolet?style=for-the-badge)

---

## 🌟 The Story Behind the Project

As a first-year student, I wanted to build something that felt like it belonged in a sci-fi movie. I noticed that most gesture controllers are "messy" — if you try to skip a song, you accidentally change the volume too.

GestureFlow started as a simple pinch-to-volume script and evolved — version by version — into a full web-native spatial interaction system. **Version 6.0** adds two entirely new dimensions of interaction: a **persistent neon drawing canvas** and a **holographic globe** you can spawn in mid-air and drag across the screen with your palm. All ten gesture states are conflict-free by design.

---

## 🚀 The Development Journey (Full Roadmap)

**📍 Version 1.0 — The Foundation**
- **Built:** Basic thumb-to-index pinch distance tracking.
- **Features:** Volume control only.
- **Lesson:** Learned OpenCV frame capture and pycaw audio API.
- **Problem:** High sensitivity — volume changed with every slight hand twitch.

**📍 Version 2.0 — The Visual UI**
- **Built:** Brightness control + real-time HUD bars on the video feed.
- **Features:** Volume and brightness bars overlaid on the live frame.
- **Lesson:** NumPy interpolation and drawing primitives on frames.
- **Problem:** System couldn't distinguish left hand from right hand.

**📍 Version 3.0 — Adding Intelligence**
- **Built:** Hand identification (handedness) and media key injection.
- **Features:** Left hand → Volume, Right hand → Brightness, Thumb Down → Minimize.
- **Lesson:** Integrated pyautogui for keyboard automation.
- **Problem:** Gesture overlap — skipping a song accidentally triggered volume changes.

**📍 Version 4.0 — The Intuitive Build**
- **Built:** A strict state machine using the middle finger as a mode toggle.
- **Features:** Middle finger UP = Level Mode, Middle finger DOWN = Navigation Mode.
- **Lesson:** State management and conditional gesture logic. Achieved near-100% accuracy.

**📍 Version 5.0 — The Web Evolution**
- **Built:** Entire system ported to a Flask web framework.
- **Features:** Real-time MJPEG video streaming to a browser dashboard, modern dark UI, shutdown controls.
- **Lesson:** Full-stack basics, MJPEG streaming, client-server architecture.

**📍 Version 6.0 — Spatial Interaction (Current)**
- **Built:** Spatial drawing canvas, geometric circle detection, holographic globe, spacebar gesture, redesigned frontend.
- **Features:** Peace sign → draw neon strokes; draw a circle in air → spawn interactive holo-globe; index + pinky → spacebar; full UI redesign with Syne/DM Sans fonts, GSAP boot sequence, glassmorphism bento layout.
- **Lesson:** NumPy overlay compositing, geometric shape recognition, animation timer-driven rendering, thread-safe shared state.

---

## ✨ Full Feature Set (v6.0)

### 🎮 Gesture State Machine — 10 States, Zero Conflicts

| Gesture | Hand | Mode Condition | Action |
| :--- | :--- | :--- | :--- |
| **Pinch** (thumb + index) | Left | Middle finger **UP** | Volume up / down |
| **Pinch** (thumb + index) | Right | Middle finger **UP** | Brightness up / down |
| **Index up only** | Right | Middle finger **DOWN** | Forward → (arrow key) |
| **Index up only** | Left | Middle finger **DOWN** | ← Backward (arrow key) |
| **Index + Pinky up** | Either | Middle finger **DOWN** | Spacebar |
| **Peace sign** (index + middle up) | Either | — | Enter Draw Mode |
| **Closed fist** | Either | Any | Mute system audio |
| **Thumb-tucked fist** | Either | Any | Win + D (show desktop) |
| **Draw a circle** in Draw Mode | Either | In Draw Mode | Spawn Holo-Globe |
| **Open palm near globe** | Either | Globe active | Drag globe across screen |

### ✍️ Spatial Drawing Canvas
- Trigger with the **peace sign** (index + middle up, ring + pinky down).
- Index fingertip becomes a neon drawing cursor.
- Strokes are painted onto a persistent NumPy overlay blended at α = 0.88 over the live video.
- Dual-line rendering: wide dim base (10 px) + bright core (4 px) = neon glow effect.
- Colour auto-cycles every 60 path points through five neon hues: **cyan → magenta → green → orange → violet**.
- Lower your hand or change gesture to stop drawing. Use the "Clear Canvas" button in the UI.

### 🌐 Holographic Globe
- Trace a **rough circle** in draw mode to trigger circle detection.
- Detection checks: ≥ 25 points, mean radius ≥ 30 px, roundness σ/μ < 0.40, closure < 1.8 × radius.
- Globe spawns at the circle's centroid with radius scaled from your drawing.
- While globe is active, **all other gesture processing is paused**.
- Hold your **open palm near the globe** to drag it around the screen.
- Globe **dissolves after 4 seconds** of no interaction — a timeout progress bar shows remaining time.
- All gestures resume automatically after the globe disappears.

### 🎨 Frontend — Redesigned in v6.0
- **Fonts:** Syne (display) + DM Sans (body) — soft, rounded, modern.
- **Layout:** CSS bento-grid with live video left-column, mode badge + level meters + controls stacked right.
- **Loading screen:** GSAP-animated 5-stage neural engine boot sequence with progress bar.
- **Live status:** JS polls `/status` every 900 ms — mode badge, volume/brightness bars, and globe pill update in real time.
- **Gesture Atlas:** All 10 gestures documented with colour-coded cards by mode category.
- **Features Spotlight:** Interactive CSS globe animation and SVG path draw animation for the new v6.0 features.

---

## 🧠 Technical Architecture

```
Webcam → OpenCV Capture → BGR→RGB → Frame Buffer
                                          │
                                    MediaPipe Hands
                                    (21 landmarks × 2 hands)
                                          │
                                   Finger State Flags
                                   (tip.y < PIP.y → up)
                                          │
                               Gesture State Machine
                          ┌──────────┬───────────┬──────────┐
                     Canvas       Circle      Holo-Globe    HUD
                     Engine      Detector     Renderer    Overlay
                          └──────────┴───────────┴──────────┘
                                          │
                          ┌───────────────┼───────────────┐
                        pycaw            sbc          pyautogui
                      (volume)      (brightness)    (keys / hotkeys)
                                          │
                                   Flask HTTP Server
                          ┌───────────────┼───────────────┐
                      /video_feed      /status       /clear_canvas
                      (MJPEG stream)  (JSON poll)    (POST reset)
                                          │
                                 Browser Frontend
                          ┌───────────────┼───────────────┐
                      <img> stream    JS 900ms poll   GSAP UI
```

### Key Technical Decisions
1. **Priority-ordered state machine** — Globe intercepts first, then Draw, then Standard gestures. The `continue` statement in globe mode hard-skips all other evaluation.
2. **Peace sign for draw** — Index + middle UP is geometrically distinct from navigation (index UP + middle strictly DOWN). No overlap possible.
3. **Thread-safe canvas** — A `threading.Lock` protects the NumPy canvas array accessed by both the frame generator and the `/clear_canvas` route.
4. **Debounce via key_delay** — A frame counter (15 frames for nav/space, 30 for Win+D) prevents a sustained gesture from firing hundreds of key events.
5. **Neon glow without shaders** — Two overlapping `cv2.line` calls (wide + dim, narrow + bright) simulate a luminous stroke on CPU.

---

## 🛠️ Setup & Installation

```bash
pip install flask opencv-python mediapipe numpy pycaw screen-brightness-control pyautogui
```

### Project Structure

```
GestureFlow/
├── app.py
└── templates/
    └── index.html
```

### Run

```bash
python app.py
```

Open **http://127.0.0.1:5000** in your browser.

> **Requirements:** Python 3.8+, Windows (pycaw is Windows-only), webcam, well-lit environment.

---

## 🎮 Quick Gesture Reference

```
LEVEL MODE  (middle finger UP)
  Left hand  pinch  →  Volume
  Right hand pinch  →  Brightness

NAVIGATION  (middle finger DOWN)
  Right index only   →  Forward →
  Left  index only   →  ← Backward
  Index + Pinky      →  [ Spacebar ]

SYSTEM
  Closed fist        →  Mute
  Thumb-tucked fist  →  Win + D

DRAW MODE  (peace sign: index + middle UP, ring + pinky DOWN)
  Move index tip     →  Paint neon stroke
  Draw a circle      →  Spawn Holo-Globe

GLOBE MODE  (auto-activates on circle detection)
  Palm near globe    →  Drag globe
  No touch 4 sec     →  Globe dissolves, gestures resume
```

---

## 👨‍💻 About

**Saiyam Bajpai** — B.Tech in Computer Science & Design @ MITS Gwalior | BS in Data Science @ IIT Madras.

This project taught me that great HCI is about removing friction between human intent and machine response — and that the best interface is the one you already have: your hands.

[![GitHub](https://img.shields.io/badge/GitHub-saiyam--bajpai-black?style=flat-square&logo=github)](https://github.com/saiyam-bajpai/Computer-Vision-based-Hand-Gesture-Control)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-saiyam--bajpai-blue?style=flat-square&logo=linkedin)](https://www.linkedin.com/in/saiyam-bajpai/)

---

> *"The best interface is no interface — but until then, your hands will do."*
