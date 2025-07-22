import cv2
import mediapipe as mp
import numpy as np
from collections import deque
import pyautogui
import time
import winsound
import os
import queue
import threading

# Inisialisasi MediaPipe Hands
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.9, min_tracking_confidence=0.9)

# Inisialisasi webcam
def find_webcam():
    """Mencari indeks webcam yang tersedia."""
    for i in range(3):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            print(f"Webcam ditemukan pada indeks {i}")
            return cap, i
        cap.release()
    return None, None

cap, index = find_webcam()
if cap is None:
    print("Error: Tidak ada webcam yang ditemukan.")
    exit()

# Smoothing dengan filter Kalman
class SimpleKalman:
    """Filter Kalman sederhana untuk smoothing jumlah jari."""
    def __init__(self, process_noise=0.002, measurement_noise=0.02):
        self.x = 0
        self.P = 1
        self.Q = process_noise
        self.R = measurement_noise

    def update(self, measurement):
        self.P = self.P + self.Q
        K = self.P / (self.P + self.R)
        self.x = self.x + K * (measurement - self.x)
        self.P = (1 - K) * self.P
        return int(round(self.x))

# Inisialisasi variabel
kalman = SimpleKalman()
fingers_up_history = deque(maxlen=4)
last_gesture_time = 0
gesture_cooldown = 1.5
pointer_active = False
calibration_mode = False
calibration_threshold = 0.04
gesture_duration = {}
gesture_duration_threshold = 3
last_fingers = -1
gesture_queue = queue.Queue()
running = True

# Log gestur
log_file = "gesture_log.txt"
if os.path.exists(log_file):
    os.remove(log_file)

def log_gesture(gesture):
    """Mencatat gestur ke file log."""
    with open(log_file, 'a') as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}: {gesture}\n")

def is_hand_upright(hand_landmarks):
    """Cek apakah tangan dalam posisi tegak."""
    wrist = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]
    middle_finger_mcp = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_MCP]
    return wrist.y > middle_finger_mcp.y

def count_fingers(hand_landmarks, frame):
    """Menghitung jumlah jari yang terangkat."""
    finger_tips = [
        mp_hands.HandLandmark.THUMB_TIP,
        mp_hands.HandLandmark.INDEX_FINGER_TIP,
        mp_hands.HandLandmark.MIDDLE_FINGER_TIP,
        mp_hands.HandLandmark.RING_FINGER_TIP,
        mp_hands.HandLandmark.PINKY_TIP
    ]
    finger_pip = [
        mp_hands.HandLandmark.THUMB_IP,
        mp_hands.HandLandmark.INDEX_FINGER_PIP,
        mp_hands.HandLandmark.MIDDLE_FINGER_PIP,
        mp_hands.HandLandmark.RING_FINGER_PIP,
        mp_hands.HandLandmark.PINKY_PIP
    ]
    finger_mcp = [
        mp_hands.HandLandmark.THUMB_MCP,
        mp_hands.HandLandmark.INDEX_FINGER_MCP,
        mp_hands.HandLandmark.MIDDLE_FINGER_MCP,
        mp_hands.HandLandmark.RING_FINGER_MCP,
        mp_hands.HandLandmark.PINKY_MCP
    ]
    
    fingers_up = 0
    upright = is_hand_upright(hand_landmarks)
    for tip, pip, mcp in zip(finger_tips, finger_pip, finger_mcp):
        tip_y = hand_landmarks.landmark[tip].y
        pip_y = hand_landmarks.landmark[pip].y
        mcp_y = hand_landmarks.landmark[mcp].y
        if upright:
            if tip_y < pip_y - calibration_threshold and tip_y < mcp_y - calibration_threshold:
                fingers_up += 1
                x = int(hand_landmarks.landmark[tip].x * frame.shape[1])
                y = int(hand_landmarks.landmark[tip].y * frame.shape[0])
                cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)
        else:
            if tip_y > pip_y + calibration_threshold and tip_y > mcp_y + calibration_threshold:
                fingers_up += 1
                x = int(hand_landmarks.landmark[tip].x * frame.shape[1])
                y = int(hand_landmarks.landmark[tip].y * frame.shape[0])
                cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)
    
    return fingers_up

def detect_ok_gesture(hand_landmarks):
    """Mendeteksi gestur OK."""
    thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
    index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
    distance = np.sqrt((thumb_tip.x - index_tip.x)**2 + (thumb_tip.y - index_tip.y)**2)
    return distance < 0.05

def detect_thumb_gesture(hand_landmarks):
    """Mendeteksi gestur jempol."""
    thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
    thumb_ip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_IP]
    upright = is_hand_upright(hand_landmarks)
    if upright:
        return thumb_tip.y < thumb_ip.y - calibration_threshold
    return thumb_tip.y > thumb_ip.y + calibration_threshold

def process_gestures():
    """Memproses gestur di thread terpisah."""
    global last_gesture_time, pointer_active, calibration_mode, calibration_threshold, last_fingers, running
    while running and cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Gagal menangkap frame dari webcam.")
            break

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(frame_rgb)

        gesture_data = {"status": "Tidak Ada Gestur", "fingers": 0, "smoothed_fingers": 0, "pointer": False}
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS,
                                         mp_drawing.DrawingSpec(color=(0, 255, 255), thickness=2),
                                         mp_drawing.DrawingSpec(color=(255, 0, 255), thickness=2))
                
                fingers_up = count_fingers(hand_landmarks, frame)
                fingers_up_history.append(fingers_up)
                if len(fingers_up_history) >= 4:
                    smoothed_fingers = kalman.update(max(set(fingers_up_history), key=fingers_up_history.count))
                else:
                    smoothed_fingers = fingers_up
                
                if smoothed_fingers != last_fingers:
                    gesture_duration.clear()
                    last_fingers = smoothed_fingers
                
                if smoothed_fingers not in gesture_duration:
                    gesture_duration[smoothed_fingers] = 0
                gesture_duration[smoothed_fingers] += 1
                if detect_ok_gesture(hand_landmarks):
                    gesture_duration['OK'] = gesture_duration.get('OK', 0) + 1
                else:
                    gesture_duration['OK'] = 0
                if detect_thumb_gesture(hand_landmarks):
                    gesture_duration['thumb'] = gesture_duration.get('thumb', 0) + 1
                else:
                    gesture_duration['thumb'] = 0

                gesture_data["fingers"] = fingers_up
                gesture_data["smoothed_fingers"] = smoothed_fingers

                if not calibration_mode:
                    current_time = time.time()
                    if current_time - last_gesture_time > gesture_cooldown:
                        if smoothed_fingers == 2 and gesture_duration[smoothed_fingers] >= gesture_duration_threshold:
                            pyautogui.press('right')
                            gesture_data["status"] = "Slide Berikutnya"
                            winsound.Beep(1000, 100)
                            log_gesture("Slide Berikutnya")
                            last_gesture_time = current_time
                            gesture_duration[smoothed_fingers] = 0
                        elif smoothed_fingers == 3 and gesture_duration[smoothed_fingers] >= gesture_duration_threshold:
                            pyautogui.press('left')
                            gesture_data["status"] = "Slide Sebelumnya"
                            winsound.Beep(800, 100)
                            log_gesture("Slide Sebelumnya")
                            last_gesture_time = current_time
                            gesture_duration[smoothed_fingers] = 0
                        elif smoothed_fingers == 5 and gesture_duration[smoothed_fingers] >= gesture_duration_threshold:
                            pyautogui.hotkey('ctrl', '+')
                            gesture_data["status"] = "Zoom In"
                            winsound.Beep(1200, 100)
                            log_gesture("Zoom In")
                            last_gesture_time = current_time
                            gesture_duration[smoothed_fingers] = 0
                        elif smoothed_fingers == 0 and gesture_duration[smoothed_fingers] >= gesture_duration_threshold:
                            pyautogui.hotkey('ctrl', '-')
                            gesture_data["status"] = "Zoom Out"
                            winsound.Beep(600, 100)
                            log_gesture("Zoom Out")
                            last_gesture_time = current_time
                            gesture_duration[smoothed_fingers] = 0
                        elif detect_ok_gesture(hand_landmarks) and gesture_duration['OK'] >= gesture_duration_threshold:
                            pyautogui.press('f5')
                            gesture_data["status"] = "Presentasi Mulai/Berhenti"
                            winsound.Beep(1500, 100)
                            log_gesture("Presentasi Mulai/Berhenti")
                            last_gesture_time = current_time
                            gesture_duration['OK'] = 0
                        elif detect_thumb_gesture(hand_landmarks) and gesture_duration['thumb'] >= gesture_duration_threshold:
                            if not pointer_active:
                                pointer_active = True
                                gesture_data["status"] = "Pointer Aktif"
                                gesture_data["pointer"] = True
                                winsound.Beep(1100, 100)
                                log_gesture("Pointer Aktif")
                                last_gesture_time = current_time
                                gesture_duration['thumb'] = 0
                            x = int(hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP].x * frame.shape[1])
                            y = int(hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP].y * frame.shape[0])
                            cv2.circle(frame, (x, y), 8, (255, 50, 50), -1)
                            screen_width, screen_height = pyautogui.size()
                            pyautogui.moveTo(x * screen_width / 640, y * screen_height / 480)
                        elif pointer_active:
                            pointer_active = False
                            gesture_data["status"] = "Pointer Nonaktif"
                            winsound.Beep(900, 100)
                            log_gesture("Pointer Nonaktif")
                            last_gesture_time = current_time
                            gesture_duration['thumb'] = 0

        try:
            gesture_queue.put_nowait((frame, gesture_data))
        except queue.Full:
            pass

def video_loop():
    """Menampilkan feed webcam dengan UI minimal."""
    global running
    while running and cap.isOpened():
        try:
            frame, _ = gesture_queue.get_nowait()
            cv2.imshow('GestureSlide Pro - Webcam', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                running = False
                break
        except queue.Empty:
            continue
    cap.release()
    cv2.destroyAllWindows()

def start_processing():
    """Memulai thread untuk pemrosesan gestur dan video."""
    gesture_thread = threading.Thread(target=process_gestures, daemon=True)
    video_thread = threading.Thread(target=video_loop, daemon=True)
    gesture_thread.start()
    video_thread.start()
    return gesture_thread, video_thread

def main():
    """Fungsi utama untuk pemrosesan gestur."""
    global running
    try:
        start_processing()
        while running:
            time.sleep(0.1)  # Menahan main thread
    except KeyboardInterrupt:
        running = False
    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    print("Harap jalankan 'python src/gui.py' untuk memulai aplikasi dengan GUI.")