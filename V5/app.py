import cv2
import mediapipe as mp
import math
import numpy as np
import screen_brightness_control as sbc
from pycaw.pycaw import AudioUtilities
import pyautogui
from flask import Flask, render_template, Response

# This ensures Flask finds the templates folder inside the sub-directory
app = Flask(__name__, template_folder='templates')

# --- INITIALIZE MEDIAPIPE ONCE ---
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

# --- INITIALIZE VOLUME ONCE ---
volume = None
try:
    devices = AudioUtilities.GetSpeakers()
    volume = devices.EndpointVolume
except:
    print("Audio device not found.")

def generate_frames():
    # Open camera inside the generator
    cap = cv2.VideoCapture(0)
    vol_bar, vol_per = 400, 0
    bright_bar, bright_per = 400, 0
    key_delay = 0

    while True:
        success, img = cap.read()
        if not success:
            break
        
        img = cv2.flip(img, 1)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = hands.process(img_rgb)

        if results.multi_hand_landmarks:
            for i, hand_lms in enumerate(results.multi_hand_landmarks):
                label = results.multi_handedness[i].classification[0].label 
                lm_list = []
                for id, lm in enumerate(hand_lms.landmark):
                    h, w, c = img.shape
                    lm_list.append([id, int(lm.x * w), int(lm.y * h)])

                if lm_list:
                    # 1. Finger States
                    is_index_up = lm_list[8][2] < lm_list[6][2]
                    is_middle_up = lm_list[12][2] < lm_list[10][2]
                    is_ring_up = lm_list[16][2] < lm_list[14][2]
                    is_pinky_up = lm_list[20][2] < lm_list[18][2]
                    is_thumb_up = lm_list[4][2] < lm_list[2][2]
                    up_count = [is_index_up, is_middle_up, is_ring_up, is_pinky_up].count(True)

                    # FEATURE: MUTE (Fist)
                    if up_count == 0 and not is_thumb_up:
                        if volume: volume.SetMute(1, None)
                        cv2.putText(img, "MUTE ACTIVE", (450, 400), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)

                    # MODE 1: LEVEL MODE (Middle Finger UP)
                    if is_middle_up:
                        x1, y1, x2, y2 = lm_list[4][1], lm_list[4][2], lm_list[8][1], lm_list[8][2]
                        length = math.hypot(x2 - x1, y2 - y1)
                        if label == 'Left':
                            vol_scalar = np.interp(length, [30, 200], [0.0, 1.0])
                            vol_per, vol_bar = vol_scalar * 100, np.interp(length, [30, 200], [400, 150])
                            if volume: 
                                volume.SetMute(0, None)
                                volume.SetMasterVolumeLevelScalar(vol_scalar, None)
                        else:
                            bright = np.interp(length, [30, 200], [0, 100])
                            bright_per, bright_bar = bright, np.interp(length, [30, 200], [400, 150])
                            try: sbc.set_brightness(int(bright))
                            except: pass
                        cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 3)

                    # MODE 2: NAVIGATION (Middle Finger DOWN)
                    else:
                        if key_delay == 0:
                            if label == 'Right' and up_count == 1 and is_index_up:
                                pyautogui.press('right')
                                cv2.putText(img, "FORWARD >>", (450, 360), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
                                key_delay = 15
                            elif label == 'Left' and up_count == 1 and is_index_up:
                                pyautogui.press('left')
                                cv2.putText(img, "<< BACKWARD", (450, 360), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)
                                key_delay = 15
                            elif lm_list[4][2] > lm_list[2][2] and up_count == 0:
                                pyautogui.hotkey('win', 'd')
                                key_delay = 30

                mp_draw.draw_landmarks(img, hand_lms, mp_hands.HAND_CONNECTIONS)

        if key_delay > 0: key_delay -= 1

        # Draw HUD Bars
        cv2.rectangle(img, (50, 150), (85, 400), (255, 0, 0), 2)
        cv2.rectangle(img, (50, int(vol_bar)), (85, 400), (255, 0, 0), cv2.FILLED)
        cv2.rectangle(img, (1180, 150), (1215, 400), (0, 255, 255), 2)
        cv2.rectangle(img, (1180, int(bright_bar)), (1215, 400), (0, 255, 255), cv2.FILLED)

        # Web Stream Encoding
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
    # Run Flask on local port 5000
    app.run(host='0.0.0.0', port=5000, debug=False)