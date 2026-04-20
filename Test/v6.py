import cv2
import mediapipe as mp
import math
import numpy as np
import screen_brightness_control as sbc
from pycaw.pycaw import AudioUtilities
import pyautogui
from flask import Flask, render_template, Response
import time

app = Flask(__name__, template_folder='templates')

# --- ENGINE INITIALIZATION ---
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.8, min_tracking_confidence=0.8)
mp_draw = mp.solutions.drawing_utils

# State Persistence
canvas = None 
points = []
globe_active = False
globe_center = (0, 0)
last_interaction = time.time()
space_cooldown = 0

try:
    devices = AudioUtilities.GetSpeakers()
    volume = devices.EndpointVolume
except:
    volume = None

def detect_circle(pts):
    if len(pts) < 20: return False
    # Check if start and end points meet
    dist = math.hypot(pts[0][0] - pts[-1][0], pts[0][1] - pts[-1][1])
    # Check "roundness" by comparing bounding box aspect ratio
    x_coords = [p[0] for p in pts]
    y_coords = [p[1] for p in pts]
    w_path = max(x_coords) - min(x_coords)
    h_path = max(y_coords) - min(y_coords)
    if dist < 70 and (0.7 < w_path/h_path < 1.3): 
        return True
    return False

def generate_frames():
    global canvas, points, globe_active, globe_center, last_interaction, space_cooldown
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    while True:
        success, img = cap.read()
        if not success: break
        
        img = cv2.flip(img, 1) # Mirror for natural interaction
        h, w, c = img.shape
        if canvas is None: canvas = np.zeros((h, w, 3), np.uint8)

        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = hands.process(img_rgb)

        if results.multi_hand_landmarks:
            for i, hand_lms in enumerate(results.multi_hand_landmarks):
                # Correct Hand Labeling (MediaPipe labels are swapped when image is flipped)
                lbl = results.multi_handedness[i].classification[0].label
                hand_type = "Left" if lbl == "Right" else "Right" 
                
                lm_list = [[id, int(lm.x * w), int(lm.y * h)] for id, lm in enumerate(hand_lms.landmark)]
                
                # Finger State Logic
                # Fingers: Index(8), Middle(12), Ring(16), Pinky(20), Thumb(4)
                f = [lm_list[8][2] < lm_list[6][2],   # Index
                     lm_list[12][2] < lm_list[10][2], # Middle
                     lm_list[16][2] < lm_list[14][2], # Ring
                     lm_list[20][2] < lm_list[18][2]] # Pinky
                thumb_up = lm_list[4][1] > lm_list[3][1] if hand_type == "Right" else lm_list[4][1] < lm_list[3][1]

                # 1. SPATIAL GLOBE INTERACTION (Override everything)
                if globe_active:
                    last_interaction = time.time()
                    globe_center = (lm_list[9][1], lm_list[9][2])
                    if sum(f) == 0 and not thumb_up: # Close fist to dismiss globe
                        globe_active = False

                else:
                    # 2. ROCK SIGN (Index + Pinky UP) -> SPACEBAR
                    if f[0] and f[3] and not f[1] and not f[2]:
                        if time.time() > space_cooldown:
                            pyautogui.press('space')
                            space_cooldown = time.time() + 0.8 # Prevent spam
                            cv2.putText(img, "SPACE", (lm_list[0][1], lm_list[0][2]-20), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                    # 3. DRAWING (Index + Middle UP)
                    elif f[0] and f[1] and not f[2]:
                        curr_pt = (lm_list[8][1], lm_list[8][2])
                        points.append(curr_pt)
                        if len(points) > 1:
                            cv2.line(canvas, points[-2], points[-1], (255, 0, 110), 8) # Punchy Neon Pink

                    # 4. CIRCLE RELEASE -> TRIGGER GLOBE
                    elif len(points) > 15:
                        if detect_circle(points):
                            globe_active = True
                            canvas = np.zeros((h, w, 3), np.uint8) # Flash clear
                        points = []

                    # 5. LEVELS (Middle Finger ONLY UP)
                    elif f[1] and not f[0]:
                        dist = math.hypot(lm_list[4][1]-lm_list[8][1], lm_list[4][2]-lm_list[8][2])
                        if hand_type == "Left":
                            vol = np.interp(dist, [20, 160], [0.0, 1.0])
                            if volume: volume.SetMasterVolumeLevelScalar(vol, None)
                        else:
                            bri = np.interp(dist, [20, 160], [0, 100])
                            sbc.set_brightness(int(bri))
                        cv2.line(img, (lm_list[4][1], lm_list[4][2]), (lm_list[8][1], lm_list[8][2]), (0, 255, 255), 3)

                    # 6. NAVIGATION (Index ONLY UP)
                    elif f[0] and not f[1]:
                        if lm_list[8][1] < w * 0.4: pyautogui.press('left')
                        elif lm_list[8][1] > w * 0.6: pyautogui.press('right')

                    # 7. MUTE (Fist)
                    elif sum(f) == 0 and not thumb_up:
                        if volume: volume.SetMute(1, None)

                mp_draw.draw_landmarks(img, hand_lms, mp_hands.HAND_CONNECTIONS)

        # Globe Physics & Auto-Timeout
        if globe_active:
            if time.time() - last_interaction > 4: globe_active = False
            # Neon Globe Effect
            for i in range(3):
                r = 100 + (i * 20)
                color = (255, 240, 0) if i%2==0 else (255, 0, 255)
                cv2.circle(img, globe_center, r, color, 2)
                cv2.circle(img, globe_center, r+2, color, 1)

        # Composite Layers
        img = cv2.addWeighted(img, 1, canvas, 1, 0)
        
        ret, buffer = cv2.imencode('.jpg', img)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

@app.route('/')
def index(): return render_template('index.html')

@app.route('/video_feed')
def video_feed(): return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)