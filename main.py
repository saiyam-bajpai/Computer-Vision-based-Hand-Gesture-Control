import cv2
import mediapipe as mp
import math
import numpy as np
import screen_brightness_control as sbc
from pycaw.pycaw import AudioUtilities
import pyautogui

# --- 1. INITIALIZATION ---
cap = cv2.VideoCapture(0)
cap.set(3, 1280) 
cap.set(4, 720)

volume = None
try:
    devices = AudioUtilities.GetSpeakers()
    volume = devices.EndpointVolume
except Exception as e:
    print(f"Audio Setup Error: {e}")

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.8)
mp_draw = mp.solutions.drawing_utils

# Visual & Control Variables
vol_bar, vol_per = 400, 0
bright_bar, bright_per = 400, 0
key_delay = 0 

print("\n--- System Ready ---")
print("1. Middle Finger UP   -> Adjust Volume/Brightness")
print("2. Middle Finger DOWN -> Navigation Mode")
print("   - Right Hand Index = FORWARD")
print("   - Left Hand Index  = BACKWARD")
print("   - Fist             = MUTE")
print("   - Thumb Down       = MINIMIZE ALL")

while True:
    success, img = cap.read()
    if not success: break
    
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
                # 1. FINGER STATES
                # Index(8), Middle(12), Ring(16), Pinky(20)
                is_index_up = lm_list[8][2] < lm_list[6][2]
                is_middle_up = lm_list[12][2] < lm_list[10][2]
                is_ring_up = lm_list[16][2] < lm_list[14][2]
                is_pinky_up = lm_list[20][2] < lm_list[18][2]
                # Thumb logic (Tip higher than base)
                is_thumb_up = lm_list[4][2] < lm_list[2][2]

                # Count how many of the 4 fingers are up
                up_count = [is_index_up, is_middle_up, is_ring_up, is_pinky_up].count(True)

                # --- FEATURE A: MUTE (Fist Detection) ---
                # If all fingers including thumb are closed
                if up_count == 0 and not is_thumb_up:
                    if volume:
                        volume.SetMute(1, None)
                        cv2.putText(img, "MUTE ACTIVE", (550, 400), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)

                # --- FEATURE B: LEVEL ADJUSTMENT (Middle Finger is UP) ---
                if is_middle_up:
                    x1, y1 = lm_list[4][1], lm_list[4][2] # Thumb
                    x2, y2 = lm_list[8][1], lm_list[8][2] # Index
                    length = math.hypot(x2 - x1, y2 - y1)

                    if label == 'Left':
                        vol_scalar = np.interp(length, [30, 200], [0.0, 1.0])
                        vol_per = vol_scalar * 100
                        vol_bar = np.interp(length, [30, 200], [400, 150])
                        if volume: 
                            volume.SetMute(0, None) # Unmute when adjusting
                            volume.SetMasterVolumeLevelScalar(vol_scalar, None)
                        cv2.putText(img, "LEVEL: VOLUME", (50, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,0,0), 2)
                    else:
                        bright = np.interp(length, [30, 200], [0, 100])
                        bright_per = bright
                        bright_bar = np.interp(length, [30, 200], [400, 150])
                        try: sbc.set_brightness(int(bright))
                        except: pass
                        cv2.putText(img, "LEVEL: BRIGHTNESS", (950, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,255), 2)
                    
                    cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 3)

                # --- FEATURE C: NAVIGATION (Middle Finger is DOWN) ---
                else:
                    if key_delay == 0:
                        # 1. FORWARD (Right Hand - Only Index Up)
                        if label == 'Right' and up_count == 1 and is_index_up:
                            pyautogui.press('right')
                            cv2.putText(img, "FORWARD >>", (550, 360), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
                            key_delay = 15
                        
                        # 2. BACKWARD (Left Hand - Only Index Up)
                        elif label == 'Left' and up_count == 1 and is_index_up:
                            pyautogui.press('left')
                            cv2.putText(img, "<< BACKWARD", (550, 360), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)
                            key_delay = 15
                        
                        # 3. MINIMIZE (Thumb DOWN + Fist)
                        elif lm_list[4][2] > lm_list[2][2] and up_count == 0:
                            pyautogui.hotkey('win', 'd')
                            cv2.putText(img, "MINIMIZE", (550, 360), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 4)
                            key_delay = 30

                mp_draw.draw_landmarks(img, hand_lms, mp_hands.HAND_CONNECTIONS)

    if key_delay > 0: key_delay -= 1

    # --- UI DRAWING ---
    cv2.rectangle(img, (50, 150), (85, 400), (255, 0, 0), 2)
    cv2.rectangle(img, (50, int(vol_bar)), (85, 400), (255, 0, 0), cv2.FILLED)
    cv2.putText(img, f'V: {int(vol_per)}%', (45, 430), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
    
    cv2.rectangle(img, (1180, 150), (1215, 400), (0, 255, 255), 2)
    cv2.rectangle(img, (1180, int(bright_bar)), (1215, 400), (0, 255, 255), cv2.FILLED)
    cv2.putText(img, f'B: {int(bright_per)}%', (1175, 430), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

    cv2.imshow("Hand Control Pro - Iteration 4", img)
    if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.release()
cv2.destroyAllWindows()