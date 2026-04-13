import cv2
import mediapipe as mp
import math
import numpy as np
import screen_brightness_control as sbc
from pycaw.pycaw import AudioUtilities
import pyautogui
from flask import Flask, render_template, Response
import time
import os

# --- INITIALIZE FLASK ---
base_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(base_dir, 'templates')
app = Flask(__name__, template_folder=template_dir)

# --- INITIALIZE MEDIAPIPE ---
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

# --- INITIALIZE SYSTEM CONTROLS ---
volume = None
try:
    devices = AudioUtilities.GetSpeakers()
    volume = devices.EndpointVolume
except: print("Audio device not found.")

# --- GLOBALS ---
canvas = None
xp, yp = 0, 0
points_buffer = []
globe_active = False
globe_timer = 0
globe_rotation = 0

def draw_neon_line(img, p1, p2, color, thickness):
    """ Creates a glowing neon line effect """
    # Draw the outer glow (thick, low opacity)
    cv2.line(img, p1, p2, color, thickness + 10, cv2.LINE_AA)
    # Draw the inner core (thin, white/bright)
    cv2.line(img, p1, p2, (255, 255, 255), thickness - 2, cv2.LINE_AA)

def detect_circle(points):
    """ Checks if the drawn points form a rough circle """
    if len(points) < 15: return False
    dist = math.hypot(points[0][0] - points[-1][0], points[0][1] - points[-1][1])
    # If start and end points are close and we have enough points
    if dist < 60:
        xs = [p[0] for p in points]
        return (max(xs) - min(xs)) > 100 # Ensure it has width
    return False

def draw_glowing_globe(img, center, rotation):
    """ Draws a 3D-style wireframe globe that glows """
    cx, cy = center
    r = 150
    color = (255, 255, 0) # Cyan Glow
    overlay = img.copy()
    
    # Longitudinal lines
    for i in range(0, 180, 30):
        angle = math.radians(i + rotation)
        w = int(r * math.cos(angle))
        cv2.ellipse(overlay, (cx, cy), (abs(w), r), 0, 0, 360, color, 2, cv2.LINE_AA)
    
    # Latitudinal lines
    for i in range(-60, 90, 30):
        ry = int(r * math.sin(math.radians(i)))
        slice_r = int(r * math.cos(math.radians(i)))
        cv2.ellipse(overlay, (cx, cy + ry), (slice_r, 4), 0, 0, 360, color, 1, cv2.LINE_AA)
    
    cv2.addWeighted(overlay, 0.7, img, 0.3, 0, img)

def generate_frames():
    global canvas, xp, yp, points_buffer, globe_active, globe_timer, globe_rotation
    
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    vol_bar, bright_bar = 400, 400
    key_delay = 0

    while True:
        success, img = cap.read()
        if not success: break
        
        img = cv2.flip(img, 1)
        h, w, c = img.shape
        if canvas is None: canvas = np.zeros((h, w, 3), np.uint8)
        
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = hands.process(img_rgb)
        mode = "IDLE"

        if results.multi_hand_landmarks:
            for hand_lms in results.multi_hand_landmarks:
                # 1. Draw COOL Skeleton Lines
                mp_draw.draw_landmarks(img, hand_lms, mp_hands.HAND_CONNECTIONS,
                                     mp_draw.DrawingSpec(color=(255, 255, 255), thickness=2, circle_radius=2),
                                     mp_draw.DrawingSpec(color=(255, 255, 0), thickness=2))
                
                lm_list = [[id, int(lm.x * w), int(lm.y * h)] for id, lm in enumerate(hand_lms.landmark)]
                
                # Finger states
                is_index_up = lm_list[8][2] < lm_list[6][2]
                is_middle_up = lm_list[12][2] < lm_list[10][2]
                is_ring_up = lm_list[16][2] < lm_list[14][2]
                is_pinky_up = lm_list[20][2] < lm_list[18][2]
                is_thumb_up = lm_list[4][2] < lm_list[2][2]
                up_count = [is_index_up, is_middle_up, is_ring_up, is_pinky_up].count(True)

                # --- NEW FEATURE: NEON DRAWING (Index + Middle UP) ---
                if is_index_up and is_middle_up and not is_ring_up:
                    mode = "SKETCH"
                    x1, y1 = lm_list[8][1], lm_list[8][2]
                    if xp == 0: xp, yp = x1, y1
                    
                    # Draw glowing line
                    draw_neon_line(canvas, (xp, yp), (x1, y1), (255, 255, 0), 6)
                    xp, yp = x1, y1
                    points_buffer.append((x1, y1))
                    
                    # Circle detection for Globe
                    if detect_circle(points_buffer):
                        globe_active = True
                        globe_timer = time.time()
                        canvas = np.zeros((h, w, 3), np.uint8) # Clear canvas
                        points_buffer = []

                # --- GLOBE LOGIC ---
                elif globe_active:
                    mode = "HOLOGRAM"
                    globe_rotation += 5
                    center = (lm_list[9][1], lm_list[9][2])
                    draw_glowing_globe(img, center, globe_rotation)
                    if time.time() - globe_timer > 10 or up_count == 0:
                        globe_active = False

                # --- OLD GESTURE: VOLUME/BRIGHTNESS (Middle UP + Pinch) ---
                elif is_middle_up:
                    mode = "LEVELS"
                    x1, y1, x2, y2 = lm_list[4][1], lm_list[4][2], lm_list[8][1], lm_list[8][2]
                    length = math.hypot(x2 - x1, y2 - y1)
                    
                    # Left side screen = Vol | Right side = Brightness
                    if lm_list[0][1] < w//2:
                        vol_scalar = np.interp(length, [30, 200], [0.0, 1.0])
                        vol_bar = np.interp(length, [30, 200], [400, 150])
                        if volume: 
                            volume.SetMute(0, None)
                            volume.SetMasterVolumeLevelScalar(vol_scalar, None)
                    else:
                        bright = np.interp(length, [30, 200], [0, 100])
                        bright_bar = np.interp(length, [30, 200], [400, 150])
                        try: sbc.set_brightness(int(bright))
                        except: pass
                    cv2.line(img, (x1, y1), (x2, y2), (255, 255, 255), 2)
                    xp, yp = 0, 0 # Reset drawing

                # --- OLD GESTURE: NAVIGATION (Middle DOWN) ---
                else:
                    xp, yp = 0, 0
                    if key_delay == 0:
                        if up_count == 1 and is_index_up:
                            # Forward/Backward
                            if lm_list[8][1] > lm_list[0][1] + 100:
                                pyautogui.press('right')
                                key_delay = 15
                            elif lm_list[8][1] < lm_list[0][1] - 100:
                                pyautogui.press('left')
                                key_delay = 15
                        elif not is_thumb_up and up_count == 0:
                            # Show Desktop (Fist but thumb tucked)
                            pyautogui.hotkey('win', 'd')
                            key_delay = 30

                # --- OLD GESTURE: MUTE (Fist) ---
                if up_count == 0 and not is_thumb_up:
                    if volume: volume.SetMute(1, None)
                    mode = "SYSTEM MUTE"

        if key_delay > 0: key_delay -= 1

        # HUD Overlay
        cv2.putText(img, f"SYSTEM STATE: {mode}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Merge Canvas with Glow
        img_gray = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY)
        _, img_inv = cv2.threshold(img_gray, 20, 255, cv2.THRESH_BINARY_INV)
        img_inv = cv2.cvtColor(img_inv, cv2.COLOR_GRAY2BGR)
        img = cv2.bitwise_and(img, img_inv)
        img = cv2.bitwise_or(img, canvas)

        # Draw Level Bars (Futuristic style)
        cv2.rectangle(img, (20, 150), (30, 400), (50, 50, 50), -1)
        cv2.rectangle(img, (20, int(vol_bar)), (30, 400), (255, 255, 0), -1)
        cv2.rectangle(img, (w-30, 150), (w-20, 400), (50, 50, 50), -1)
        cv2.rectangle(img, (w-30, int(bright_bar)), (w-20, 400), (0, 255, 255), -1)

        ret, buffer = cv2.imencode('.jpg', img)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)