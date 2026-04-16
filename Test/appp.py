import cv2
import mediapipe as mp
import math
import numpy as np
import screen_brightness_control as sbc
from pycaw.pycaw import AudioUtilities
import pyautogui
from flask import Flask, render_template, Response, jsonify
import time
import threading

# Flask app — template folder stays at 'templates'
app = Flask(__name__, template_folder='templates')

# ─────────────────────────────────────────────────────────────────────────────
#  MEDIAPIPE INIT
# ─────────────────────────────────────────────────────────────────────────────
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

HAND_CONN_SPEC = mp_draw.DrawingSpec(color=(0, 220, 200), thickness=2, circle_radius=3)
LANDMARK_SPEC  = mp_draw.DrawingSpec(color=(255, 255, 255), thickness=2, circle_radius=4)

# ─────────────────────────────────────────────────────────────────────────────
#  AUDIO INIT
# ─────────────────────────────────────────────────────────────────────────────
volume = None
try:
    devices = AudioUtilities.GetSpeakers()
    volume = devices.EndpointVolume
except Exception:
    print("Audio device not found — volume control disabled.")

# ─────────────────────────────────────────────────────────────────────────────
#  DRAWING STATE  (global, shared with /status route)
# ─────────────────────────────────────────────────────────────────────────────
canvas_lock = threading.Lock()
canvas          = None          # numpy overlay, created on first frame
prev_draw_point = None
draw_path       = []            # accumulated points in current stroke
was_in_draw_mode = False

# Neon palette that cycles while drawing
DRAW_COLORS = [
    (0, 255, 240),    # electric cyan
    (255, 0, 220),    # vivid magenta
    (0, 255, 110),    # neon green
    (255, 140, 0),    # hot orange
    (160, 0, 255),    # deep violet
]

# ─────────────────────────────────────────────────────────────────────────────
#  GLOBE STATE
# ─────────────────────────────────────────────────────────────────────────────
globe_active       = False
globe_pos          = [640, 360]
globe_radius       = 90
globe_last_touched = 0.0
GLOBE_TIMEOUT      = 4.0        # seconds before globe fades out
globe_alpha        = 0.0        # fade-in / fade-out scalar [0..1]

# ─────────────────────────────────────────────────────────────────────────────
#  STATUS (exposed to /status endpoint)
# ─────────────────────────────────────────────────────────────────────────────
g_mode   = 'IDLE'
g_vol    = 0.0
g_bright = 0.0
g_hands  = 0
g_globe  = False


# ─────────────────────────────────────────────────────────────────────────────
#  HELPER — CIRCLE DETECTION
# ─────────────────────────────────────────────────────────────────────────────
def detect_circle(points, tolerance=0.40):
    """
    Returns (is_circle, center_tuple, mean_radius).
    Checks that:
      1. Enough points (>= 25)
      2. Mean radius >= 30 px (not a tiny scribble)
      3. Normalised std dev of radii < tolerance  (roundness)
      4. Path closure: distance from first to last point < 1.8 × mean_r
    """
    if len(points) < 25:
        return False, None, None

    pts    = np.array(points, dtype=np.float32)
    cx, cy = pts[:, 0].mean(), pts[:, 1].mean()

    radii   = np.sqrt((pts[:, 0] - cx) ** 2 + (pts[:, 1] - cy) ** 2)
    mean_r  = radii.mean()
    std_r   = radii.std()

    if mean_r < 30:
        return False, None, None

    closure = math.hypot(points[0][0] - points[-1][0],
                         points[0][1] - points[-1][1])

    is_closed    = closure < mean_r * 1.8
    is_round     = (std_r / mean_r) < tolerance

    return is_closed and is_round, (int(cx), int(cy)), int(mean_r)


# ─────────────────────────────────────────────────────────────────────────────
#  HELPER — HOLOGRAPHIC GLOBE RENDERER
# ─────────────────────────────────────────────────────────────────────────────
def draw_holographic_globe(img, center, radius, t, alpha=1.0):
    """Renders an animated holographic globe onto img (in-place)."""
    cx, cy = center
    a = max(0.0, min(1.0, alpha))

    # ── translucent sphere fill ──
    overlay = img.copy()
    cv2.circle(overlay, (cx, cy), radius, (0, 18, 28), cv2.FILLED)
    cv2.addWeighted(overlay, 0.45 * a, img, 1 - 0.45 * a, 0, img)

    # ── outer glow rings ──
    for i in range(4, 0, -1):
        r   = radius + i * 7
        col = (0, int(200 * a * i / 4), int(160 * a * i / 4))
        cv2.circle(img, (cx, cy), r, col, 1)

    # ── equator + latitude lines ──
    lat_offsets = [-0.72, -0.42, 0.0, 0.42, 0.72]
    for lat in lat_offsets:
        y_off  = int(lat * radius)
        y      = cy + y_off
        if abs(y_off) >= radius:
            continue
        a_lat  = int(math.sqrt(max(1, radius ** 2 - y_off ** 2)))
        b_lat  = max(1, int(a_lat * 0.28))
        thick  = 2 if lat == 0.0 else 1
        color  = (0, int(220 * a), int(180 * a)) if lat == 0.0 \
                 else (0, int(140 * a), int(110 * a))
        cv2.ellipse(img, (cx, y), (a_lat, b_lat), 0, 0, 360, color, thick)

    # ── animated longitude arcs ──
    for i in range(4):
        spin   = (t * 22 + i * 45) % 180
        a_lon  = max(3, int(abs(math.cos(math.radians(spin))) * radius))
        cv2.ellipse(img, (cx, cy), (a_lon, radius), int(spin),
                    0, 360, (0, int(170 * a), int(210 * a)), 1)

    # ── horizontal scan line ──
    scan_y = cy + int(math.sin(t * 2.0) * radius * 0.95)
    scan_y = max(cy - radius, min(cy + radius, scan_y))
    x_off  = int(math.sqrt(max(0, radius ** 2 - (scan_y - cy) ** 2)))
    cv2.line(img, (cx - x_off, scan_y), (cx + x_off, scan_y),
             (0, int(255 * a), int(200 * a)), 1)

    # ── hard border ──
    cv2.circle(img, (cx, cy), radius,     (0, int(230 * a), int(190 * a)), 2)
    cv2.circle(img, (cx, cy), radius + 4, (0, int(80  * a), int(60  * a)), 1)

    # ── centre dot ──
    cv2.circle(img, (cx, cy), 4, (0, int(255 * a), int(200 * a)), cv2.FILLED)

    # ── label ──
    cv2.putText(img, "HOLO-GLOBE",
                (cx - 60, cy + radius + 32),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65,
                (0, int(190 * a), int(150 * a)), 1, cv2.LINE_AA)

    # ── timeout progress bar ──
    remaining  = max(0.0, GLOBE_TIMEOUT - (time.time() - globe_last_touched))
    bar_total  = 200
    bar_filled = int((remaining / GLOBE_TIMEOUT) * bar_total)
    bx         = cx - 100
    by         = cy + radius + 44
    cv2.rectangle(img, (bx, by), (bx + bar_total, by + 8),
                  (0, int(60 * a), int(50 * a)), cv2.FILLED)
    cv2.rectangle(img, (bx, by), (bx + bar_filled, by + 8),
                  (0, int(220 * a), int(170 * a)), cv2.FILLED)
    cv2.rectangle(img, (bx, by), (bx + bar_total, by + 8),
                  (0, int(100 * a), int(80 * a)), 1)

    return img


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN FRAME GENERATOR
# ─────────────────────────────────────────────────────────────────────────────
def generate_frames():
    global canvas, prev_draw_point, draw_path, was_in_draw_mode
    global globe_active, globe_pos, globe_radius, globe_last_touched, globe_alpha
    global g_mode, g_vol, g_bright, g_hands, g_globe

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    vol_bar, vol_per     = 400, 0.0
    bright_bar, bright_per = 400, 0.0
    key_delay = 0
    anim_t    = 0.0       # animation timer (incremented each frame)

    while True:
        success, img = cap.read()
        if not success:
            break

        img = cv2.flip(img, 1)
        h, w, _ = img.shape
        anim_t  += 0.05

        # ── initialise / resize canvas ──
        with canvas_lock:
            if canvas is None or canvas.shape[:2] != (h, w):
                canvas = np.zeros((h, w, 3), dtype=np.uint8)

        # ── composite drawing canvas onto live frame ──
        with canvas_lock:
            local_canvas = canvas.copy()
        img = cv2.addWeighted(img, 1.0, local_canvas, 0.88, 0)

        # ── globe timeout check ──
        if globe_active:
            if time.time() - globe_last_touched > GLOBE_TIMEOUT:
                globe_active = False
                globe_alpha  = 0.0
                g_globe      = False
            else:
                globe_alpha = min(1.0, globe_alpha + 0.08)

        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = hands.process(img_rgb)

        in_draw_mode_this_frame = False
        g_hands = len(results.multi_hand_landmarks) if results.multi_hand_landmarks else 0

        # ── per-hand gesture processing ──
        if results.multi_hand_landmarks:
            for i, hand_lms in enumerate(results.multi_hand_landmarks):
                label   = results.multi_handedness[i].classification[0].label
                lm_list = [[id,
                            int(lm.x * w),
                            int(lm.y * h)]
                           for id, lm in enumerate(hand_lms.landmark)]

                if not lm_list:
                    continue

                # ── finger extension flags ──
                is_index_up  = lm_list[8][2]  < lm_list[6][2]
                is_middle_up = lm_list[12][2] < lm_list[10][2]
                is_ring_up   = lm_list[16][2] < lm_list[14][2]
                is_pinky_up  = lm_list[20][2] < lm_list[18][2]
                is_thumb_up  = lm_list[4][2]  < lm_list[2][2]
                up_count     = [is_index_up, is_middle_up,
                                is_ring_up,  is_pinky_up].count(True)

                # ════════════════════════════════════════════════════════════
                #  GLOBE MODE — intercepts ALL other gestures while active
                # ════════════════════════════════════════════════════════════
                if globe_active:
                    palm_x = lm_list[9][1]
                    palm_y = lm_list[9][2]
                    dist   = math.hypot(palm_x - globe_pos[0],
                                        palm_y - globe_pos[1])
                    if dist < globe_radius * 2.8:
                        globe_pos[0]   = palm_x
                        globe_pos[1]   = palm_y
                        globe_last_touched = time.time()
                    mp_draw.draw_landmarks(img, hand_lms, mp_hands.HAND_CONNECTIONS,
                                           LANDMARK_SPEC, HAND_CONN_SPEC)
                    continue   # ← skip ALL further gesture logic

                # ════════════════════════════════════════════════════════════
                #  DRAW MODE — ring + pinky UP, index + middle DOWN
                #  (unique gesture; does not clash with any existing command)
                # ════════════════════════════════════════════════════════════
                is_draw_gesture = (is_ring_up and is_pinky_up
                                   and not is_index_up and not is_middle_up)

                if is_draw_gesture:
                    in_draw_mode_this_frame = True

                    # Cycle colour through the neon palette
                    color_idx   = (len(draw_path) // 60) % len(DRAW_COLORS)
                    draw_color  = DRAW_COLORS[color_idx]
                    dim_color   = tuple(max(0, c // 3) for c in draw_color)

                    draw_x, draw_y = lm_list[8][1], lm_list[8][2]  # index-tip cursor

                    with canvas_lock:
                        if prev_draw_point is not None:
                            # Thick glow base + bright core
                            cv2.line(canvas, prev_draw_point, (draw_x, draw_y),
                                     dim_color, 10)
                            cv2.line(canvas, prev_draw_point, (draw_x, draw_y),
                                     draw_color, 4)

                    prev_draw_point = (draw_x, draw_y)
                    draw_path.append((draw_x, draw_y))

                    # On-screen cursor ring
                    cv2.circle(img, (draw_x, draw_y), 14, draw_color, 2)
                    cv2.circle(img, (draw_x, draw_y), 4,  draw_color, cv2.FILLED)
                    cv2.putText(img, "DRAW", (draw_x + 18, draw_y - 12),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, draw_color, 2, cv2.LINE_AA)
                    g_mode = 'DRAW'

                # ════════════════════════════════════════════════════════════
                #  STANDARD GESTURE LOGIC  (unchanged from original)
                # ════════════════════════════════════════════════════════════
                else:
                    prev_draw_point = None   # reset draw cursor when not drawing

                    # ── MUTE (closed fist) ──
                    if up_count == 0 and not is_thumb_up:
                        if volume:
                            volume.SetMute(1, None)
                        cv2.putText(img, "MUTE ACTIVE",
                                    (int(w / 2) - 100, 400),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1.5,
                                    (0, 0, 255), 3, cv2.LINE_AA)
                        g_mode = 'MUTE'

                    # ── LEVEL MODE (middle finger up) ──
                    if is_middle_up:
                        x1, y1 = lm_list[4][1], lm_list[4][2]   # thumb tip
                        x2, y2 = lm_list[8][1], lm_list[8][2]   # index tip
                        length = math.hypot(x2 - x1, y2 - y1)

                        if label == 'Left':
                            vol_scalar = np.interp(length, [30, 200], [0.0, 1.0])
                            vol_per    = vol_scalar * 100
                            vol_bar    = np.interp(length, [30, 200], [400, 150])
                            if volume:
                                volume.SetMute(0, None)
                                volume.SetMasterVolumeLevelScalar(vol_scalar, None)
                            g_vol  = vol_per
                            g_mode = 'LEVEL — VOL'
                        else:
                            bright     = np.interp(length, [30, 200], [0, 100])
                            bright_per = bright
                            bright_bar = np.interp(length, [30, 200], [400, 150])
                            try:
                                sbc.set_brightness(int(bright))
                            except Exception:
                                pass
                            g_bright = bright_per
                            g_mode   = 'LEVEL — BRI'

                        cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 3)

                    # ── NAVIGATION MODE (middle down, index up) ──
                    else:
                        if key_delay == 0:
                            if label == 'Right' and up_count == 1 and is_index_up:
                                pyautogui.press('right')
                                cv2.putText(img, "FORWARD >>",
                                            (w - 350, 360),
                                            cv2.FONT_HERSHEY_SIMPLEX, 1.5,
                                            (0, 255, 0), 3, cv2.LINE_AA)
                                key_delay = 15
                                g_mode    = 'NAV — FWD'

                            elif label == 'Left' and up_count == 1 and is_index_up:
                                pyautogui.press('left')
                                cv2.putText(img, "<< BACKWARD",
                                            (50, 360),
                                            cv2.FONT_HERSHEY_SIMPLEX, 1.5,
                                            (0, 0, 255), 3, cv2.LINE_AA)
                                key_delay = 15
                                g_mode    = 'NAV — BWD'

                            # ── SHOW DESKTOP (tucked-thumb fist) ──
                            elif lm_list[4][2] > lm_list[2][2] and up_count == 0:
                                pyautogui.hotkey('win', 'd')
                                key_delay = 30
                                g_mode    = 'WIN+D'

                mp_draw.draw_landmarks(img, hand_lms, mp_hands.HAND_CONNECTIONS,
                                       LANDMARK_SPEC, HAND_CONN_SPEC)

        # ── no hands detected ──
        else:
            prev_draw_point = None
            if not globe_active:
                g_mode = 'IDLE'

        # ─────────────────────────────────────────────────────────────────
        #  DRAW MODE EXIT — circle detection triggers Holo-Globe spawn
        # ─────────────────────────────────────────────────────────────────
        if was_in_draw_mode and not in_draw_mode_this_frame:
            if len(draw_path) > 20 and not globe_active:
                ok, center, r = detect_circle(draw_path)
                if ok:
                    globe_active       = True
                    globe_pos          = list(center)
                    globe_radius       = max(55, min(r, 160))
                    globe_last_touched = time.time()
                    globe_alpha        = 0.0
                    g_globe            = True
                    # Clear the canvas stroke that formed the circle
                    with canvas_lock:
                        canvas = np.zeros((h, w, 3), dtype=np.uint8)
            draw_path = []

        was_in_draw_mode = in_draw_mode_this_frame

        # ─────────────────────────────────────────────────────────────────
        #  HUD OVERLAYS
        # ─────────────────────────────────────────────────────────────────
        if key_delay > 0:
            key_delay -= 1

        # Draw mode status banner
        if in_draw_mode_this_frame:
            color_idx  = (len(draw_path) // 60) % len(DRAW_COLORS)
            draw_color = DRAW_COLORS[color_idx]
            cv2.putText(img, "◉ DRAW MODE — ring+pinky up",
                        (int(w / 2) - 200, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.85, draw_color, 2, cv2.LINE_AA)

        # Globe mode status banner
        if globe_active:
            g_globe = True
            g_mode  = 'GLOBE'
            cv2.putText(img, "◈  HOLO-GLOBE  —  ALL GESTURES PAUSED",
                        (int(w / 2) - 270, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.85,
                        (0, int(230 * globe_alpha), int(180 * globe_alpha)),
                        2, cv2.LINE_AA)
            img = draw_holographic_globe(img, tuple(globe_pos),
                                         globe_radius, anim_t, globe_alpha)

        # Volume bar (left)
        cv2.rectangle(img, (50, 150),    (85, 400), (220, 0, 80), 2)
        cv2.rectangle(img, (50, int(vol_bar)), (85, 400), (220, 0, 80), cv2.FILLED)
        cv2.putText(img, 'VOL', (42, 142), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (220, 0, 80),  1)
        cv2.putText(img, f'{int(vol_per)}%', (38, 420),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (220, 0, 80), 1)

        # Brightness bar (right)
        rbx = w - 100
        cv2.rectangle(img, (rbx, 150),    (rbx + 35, 400), (0, 220, 200), 2)
        cv2.rectangle(img, (rbx, int(bright_bar)), (rbx + 35, 400),
                      (0, 220, 200), cv2.FILLED)
        cv2.putText(img, 'BRI', (rbx - 5, 142), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 220, 200), 1)
        cv2.putText(img, f'{int(bright_per)}%', (rbx - 10, 420),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 220, 200), 1)

        # ─────────────────────────────────────────────────────────────────
        #  ENCODE + YIELD
        # ─────────────────────────────────────────────────────────────────
        ret, buffer = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 85])
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


# ─────────────────────────────────────────────────────────────────────────────
#  FLASK ROUTES
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/status')
def get_status():
    """Lightweight JSON endpoint polled by the frontend every second."""
    return jsonify({
        'mode':       g_mode,
        'volume':     round(g_vol),
        'brightness': round(g_bright),
        'hands':      g_hands,
        'globe':      g_globe,
    })


@app.route('/clear_canvas', methods=['POST'])
def clear_canvas():
    """Clears the drawing canvas overlay."""
    global canvas
    with canvas_lock:
        canvas = None          # will be re-created as blank on next frame
    return jsonify({'status': 'cleared'})


@app.route('/shutdown', methods=['POST'])
def shutdown():
    """Graceful shutdown signal (used by frontend shutdown button)."""
    import os, signal
    os.kill(os.getpid(), signal.SIGTERM)
    return jsonify({'status': 'shutting_down'})


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
