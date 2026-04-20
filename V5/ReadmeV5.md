# 🖐️ GestureFlow v5.0: The Web-AI Interface
### *A B.Tech CSD(Computer Science & Design) 1st Year Project in Human-Computer Interaction*

![Python](https://img.shields.io/badge/Made%20with-Python-blue?style=for-the-badge&logo=python)
![MediaPipe](https://img.shields.io/badge/AI-MediaPipe-brightgreen?style=for-the-badge)
![Flask](https://img.shields.io/badge/Framework-Flask-lightgrey?style=for-the-badge&logo=flask)
![Status](https://img.shields.io/badge/Status-Version_5.0_Web-blueviolet?style=for-the-badge)

## 🌟 The Story Behind the Project
As a first-year student, I wanted to build something that felt like it belonged in a sci-fi movie. I noticed that most gesture controllers are "messy"—if you try to skip a song, you accidentally change the volume too. 

In this final **Version 5.0**, I broke out of the local terminal window and transformed the project into a **Web Dashboard**. By integrating a **Flask backend** with a **modern HTML/CSS frontend**, I created a system that streams AI-processed video directly to a browser, making it feel like a professional software product rather than just a script.

---

## 🚀 The Development Journey (Roadmap)

**📍 Version 1.0: The Foundation**
*   **Built:** A basic script tracking the distance between thumb and index finger.
*   **Features:** Basic Volume Control.
*   **Lesson:** Learned `OpenCV` and `Pycaw`.
*   **Problem:** High sensitivity; volume changed with every slight hand movement.

**📍 Version 2.0: The Visual UI**
*   **Built:** Added brightness control and visual HUD bars.
*   **Features:** Real-time Volume/Brightness bars on the video feed.
*   **Lesson:** Learned `NumPy` interpolation and drawing on frames.
*   **Problem:** The system couldn't distinguish between Left and Right hands.

**📍 Version 3.0: Adding "Intelligence"**
*   **Built:** Introduced Hand Identification (Handedness) and Media Keys.
*   **Features:** Left Hand (Volume), Right Hand (Brightness), Thumb Down (Minimize).
*   **Lesson:** Integrated `PyAutoGUI` for keyboard automation.
*   **Problem:** Gesture overlap; skipping a song would accidentally trigger volume changes.

**📍 Version 4.0: The Intuitive Build**
*   **Built:** A "Strict Mode" system using state management.
*   **Features:** **Middle Finger Toggle**. Adjusting levels only works when the middle finger is up; Media controls only work when it's down.
*   **Lesson:** Learned State Management and Conditional Logic. Resulted in 100% accuracy.

**📍 Version 5.0: The Web Evolution (Current)**
*   **Built:** Integrated the entire system into a **Flask Web Framework**.
*   **Features:** Real-time video streaming to a browser-based Dashboard, Modern Dark-UI, and Shutdown controls.
*   **Lesson:** Learned **Full-Stack basics**, MJPEG streaming, and Client-Server architecture.

---

## ✨ Advanced Features
*   **🌐 Web Dashboard:** Access the controller via any browser at `localhost:5000`.
*   **🎯 Mode-Aware Adjustment:**
    *   **Middle Finger UP:** Level Mode (Pinch to change Volume/Brightness).
    *   **Middle Finger DOWN:** Navigation Mode (Index up for Forward/Back).
*   **🔊 Smart Hardware Control:** Precision volume (Left) and brightness (Right) control.
*   **⏯️ Intuitive Navigation:**
    *   **Right Hand (1 Finger):** Forward >>
    *   **Left Hand (1 Finger):** << Backward
*   **🤫 Quick Actions:**
    *   **Fist:** Mute System.
    *   **Thumb Down:** Minimize All Windows (`Win + D`).

---

## 🧠 The Technical "Brain"
1.  **The Backend (Python/Flask):** Processes the webcam feed, runs the MediaPipe AI, and triggers system hardware commands.
2.  **Video Streaming:** Uses a generator function to stream MJPEG frames to the HTML `<img>` tag.
3.  **HCI Logic:** Uses the **Middle Finger** as a physical "toggle switch" to prevent gesture overlap.
4.  **Debouncing:** A frame-based **Key Delay** prevents accidental repeated keypresses.

---

## 🛠️ Setup & Installation
```bash
# Install all the "organs" of the project
python -m pip install flask opencv-python mediapipe numpy pycaw screen-brightness-control pyautogui
```
  
### Project Structure:
```text
GestureFlowWeb/
├── app.py              (Backend)
└── templates/
    └── index.html      (Frontend)
```

### 🚀 How to Run

#### To run the Terminal Version (v4.0):
1. `cd v4_Terminal_Version`
2. `python main.py`

#### To run the Web Dashboard (v5.0):
1. `cd v5_Web_Dashboard`
2. `python app.py`
3. Open `http://127.0.0.1:5000` in your browser.

---

## 🎮 The Gesture Cheat-Sheet
| Gesture | Hand | Mode (Middle Finger) | Action |
| :--- | :--- | :--- | :--- |
| **Pinch** | Left | **UP** | Volume Up/Down |
| **Pinch** | Right | **UP** | Brightness Up/Down |
| **Index Up** | Right | **DOWN** | Forward >> |
| **Index Up** | Left | **DOWN** | << Backward |
| **Fist** | Any | Any | **MUTE** |
| **Thumb Down**| Any | **DOWN** | Minimize All |

---

## 👨‍💻 About Me
I am **Saiyam Bajpai**, a student at the intersection of Design and Data Science. I am currently pursuing my B.Tech in **Computer Science & Design** at **MITS Gwalior** and a BS in **Data Science** at **IIT Madras**. 

This project taught me that coding isn't just about syntax—it's about building bridges between human intent and machine execution.

**Let's Connect!**
*   **Focus:** Mastering Python, Computer Vision, and Full-Stack Development.
*   **Goal:** To build AI tools that make technology feel invisible and natural.

---

### ⭐ "If you can imagine it, you can code it."
*Building this roadmap taught me more about logic than any textbook ever could.*
