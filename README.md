# 🖐️ GestureFlow: The AI-Powered System Pilot
### *A B.Tech CSE 1st Year Project in Human-Computer Interaction*

![Python](https://img.shields.io/badge/Made%20with-Python-blue?style=for-the-badge&logo=python)
![MediaPipe](https://img.shields.io/badge/AI-MediaPipe-brightgreen?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Version_3.0-orange?style=for-the-badge)

## 🌟 The Story Behind the Project
As a first-year student, I wanted to build something that felt like it belonged in a sci-fi movie. I noticed that most gesture controllers are "messy"—if you try to skip a song, you accidentally change the volume too. 

In this version (**v4.0**), I solved that problem by implementing **Mode Switching Logic**. The system now understands the "context" of your hand, making the controls precise, smooth, and actually usable in daily life.

---
🚀 The Development Journey (Roadmap)
I built this project in four distinct stages, learning something new at every step. Here is how GestureFlow evolved:

**📍 Version 1.0: The Foundation**

What I built: A basic script that opened the webcam and tracked the distance between the thumb and index finger.
Features: Only Volume Control.
Learning Milestone: I learned how to use OpenCV for video frames and the Pycaw library to talk to the Windows Audio Engine.
The Problem: The volume would change every time I moved my hand, even if I wasn't trying to adjust it. It was too sensitive.

**📍 Version 2.0: The Visual UI**

What I built: Added screen brightness and a visual interface.
Features: Added Brightness Control and the Volume Bar/Percentage display on the screen.
Learning Milestone: I learned how to draw on a live video feed using cv2.rectangle and cv2.putText, and how to use NumPy to map pixel distances to percentages.
The Problem: I could control volume and brightness, but the computer couldn't tell my left hand from my right hand. It was confusing!

**📍 Version 3.0: Adding "Intelligence"**

What I built: Introduced Hand Identification (Handedness) and the first Media Keys.
Features: Left hand for Volume, Right hand for Brightness. Added Minimize (Thumb Down) and Forward/Backward gestures.
Learning Milestone: I integrated PyAutoGUI for keyboard automation. I also discovered the "AttributeError" bug when naming files mediapipe.py!
The Problem (The "Messy" Gesture): Every time I tried to use the "Peace Sign" to skip a video, the volume would also jump. The gestures were overlapping.

**📍 Version 4.0: The Final Intuitive Build (Current)**

What I built: A "Strict Mode" system with hand-specific navigation.
Features:
Mode Switch: I used the Middle Finger as a lock. Level adjustments ONLY work if the middle finger is up.
Hand Separation: Backward is now exclusively on the Left Hand, and Forward is on the Right Hand.
Fist to Mute: Added a safety mute feature when the hand is closed.
Learning Milestone: I learned State Management and Conditional Logic. By separating the logic into "Level Mode" and "Navigation Mode," I achieved 100% accuracy with zero overlap.
Result: A polished, user-friendly tool that feels like a real product.

## ✨ Advanced Features
*   **🎯 Mode-Aware Adjustment:**
    *   **Middle Finger Tucked:** Level Adjustment Mode (Volume/Brightness).
    *   **Middle Finger Up:** Media Navigation Mode (Forward/Back).
*   **🔊 Smart Volume (Left Hand):** Precision scalar control using your thumb and index finger.
*   **☀️ Adaptive Brightness (Right Hand):** Instant screen dimming or brightening.
*   **⏯️ Media Control (Right Hand):**
    *   **Peace Sign (2 Fingers):** Skip Forward (Right Arrow).
    *   **3 Fingers Up:** Skip Backward (Left Arrow).
*   **🖥️ The "Boss Key" (Thumb Down):** Instantly minimizes all windows (`Win + D`) if you point your thumb down in a fist.

---

## 🧠 The Technical "Brain"
This project goes beyond simple image detection. Here is the logic I implemented:
1.  **The Detector:** Uses Google’s `MediaPipe` to track 21 coordinates on each hand.
2.  **The Guard (State Management):** I used the **Middle Finger** as a "toggle switch." When the middle finger is down, the code freezes the media controls to prevent accidental skips while adjusting volume.
3.  **Keyboard Automation:** Uses `PyAutoGUI` to bridge the gap between "Visual Gestures" and "System Keys."
4.  **Debouncing:** I added a frame-based **Key Delay** (cooldown timer) so that one gesture doesn't trigger 50 keypresses in one second.

---

## 🛠️ Setup & Installation
To run this on your system, you need Python installed. Run the following command to install all the "organs" of the project:

```bash
python -m pip install opencv-python 
```
```bash
python -m pip install mediapipe 
```
```bash
python -m pip install numpy 
```
```bash
python -m pip install pycaw
```
```bash
python -m pip install screen-brightness-control
```
```bash
python -m pip install pyautogui
```
  
### To Run:
1. Save the final code as `main.py`.
2. Execute via terminal: `python main.py`.

---

## 🎮 The Gesture Cheat-Sheet
| Gesture | Hand | Action | Requirement |
| :--- | :--- | :--- | :--- |
| **Pinch** | Left | Volume Up/Down | Middle Finger Tucked |
| **Pinch** | Right | Brightness Up/Down | Middle Finger Tucked |
| **Peace Sign** | Right | Media Forward | Middle Finger Up |
| **3 Fingers** | Right | Media Backward | Middle Finger Up |
| **Thumb Down** | Either | Minimize All | Fingers in a Fist |

---

## 🚧 Challenges I Solved
*   **Feature Overlap:** Initially, moving fingers for media would trigger volume changes. I fixed this by creating **Conditional Logic** based on the state of the middle finger.
*   **Hardware Speed:** I calibrated the `key_delay` to ensure that media skipping feels snappy but controlled.
*   **Handedness Inversion:** Fixed the "Mirror Effect" where the camera saw the left hand as the right.

---

## 👨‍💻 About Me
I am a **1st Year B.Tech CSE student** passionate about Computer Vision and Automation. This project taught me that coding isn't just about syntax—it's about solving the "friction" between humans and machines.

**Let's Connect!**
*   **Name:** [Saiyam Bajpai]
*   **College:** [BTECH Computer Science & Design (MITS GWALIOR) | BS Data Science (IIT MADRAS)]
*   **Current Focus:** Mastering Python and exploring Deep Learning.

---

### ⭐ If you found this project cool, give it a star! 
*Building this taught me more about logic than any textbook ever could.*

---

### **How to "Download" this:**
1. Copy the text above.
2. Open your project folder.
3. Create a file named **`README.md`**.
4. Paste and Save. 
