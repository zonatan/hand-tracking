import cv2
import mediapipe as mp
import numpy as np
from collections import deque
import pyautogui
import time

# Inisialisasi MediaPipe Hands
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.9, min_tracking_confidence=0.9)

# Inisialisasi webcam
def find_webcam():
    for i in range(3):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            print(f"Webcam ditemukan pada indeks {i}")
            return cap, i
        cap.release()
    return None, None

cap, index = find_webcam()
if cap is None:
    print("Error: Tidak ada webcam yang ditemukan. Pastikan webcam terhubung dan tidak digunakan aplikasi lain.")
    exit()

# Smoothing dengan filter Kalman sederhana
class SimpleKalman:
    def __init__(self, process_noise=0.01, measurement_noise=0.1):
        self.x = 0  # Estimasi awal
        self.P = 1  # Error covariance awal
        self.Q = process_noise  # Process noise
        self.R = measurement_noise  # Measurement noise

    def update(self, measurement):
        # Prediksi
        self.P = self.P + self.Q
        # Update
        K = self.P / (self.P + self.R)  # Kalman gain
        self.x = self.x + K * (measurement - self.x)
        self.P = (1 - K) * self.P
        return int(round(self.x))

# Inisialisasi Kalman untuk smoothing jumlah jari
kalman = SimpleKalman()

# Buffer untuk mencegah gestur berulang
last_gesture_time = 0
gesture_cooldown = 1.0  # Detik

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
            if tip_y < pip_y - 0.04 and tip_y < mcp_y - 0.04:
                fingers_up += 1
                x = int(hand_landmarks.landmark[tip].x * frame.shape[1])
                y = int(hand_landmarks.landmark[tip].y * frame.shape[0])
                cv2.circle(frame, (x, y), 8, (0, 255, 0), -1)
        else:
            if tip_y > pip_y + 0.04 and tip_y > mcp_y + 0.04:
                fingers_up += 1
                x = int(hand_landmarks.landmark[tip].x * frame.shape[1])
                y = int(hand_landmarks.landmark[tip].y * frame.shape[0])
                cv2.circle(frame, (x, y), 8, (0, 255, 0), -1)
    
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
        return thumb_tip.y < thumb_ip.y - 0.04
    return thumb_tip.y > thumb_ip.y + 0.04

def main():
    try:
        # Kurangi resolusi untuk performa
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        pyautogui.FAILSAFE = True  # Gerakkan mouse ke sudut kiri atas untuk hentikan

        # Buffer untuk smoothing
        fingers_up_history = deque(maxlen=7)
        pointer_active = False

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                print("Gagal menangkap frame dari webcam.")
                break

            # Konversi frame ke RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(frame_rgb)

            # Gambar UI dasar
            cv2.rectangle(frame, (10, 10, 300, 120), (50, 50, 50), -1)  # Kotak status
            cv2.putText(frame, "GestureSlide", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS,
                                             mp_drawing.DrawingSpec(color=(0, 255, 255), thickness=2),
                                             mp_drawing.DrawingSpec(color=(255, 0, 255), thickness=2))
                    
                    # Hitung jari
                    fingers_up = count_fingers(hand_landmarks, frame)
                    fingers_up_history.append(fingers_up)
                    smoothed_fingers = kalman.update(max(set(fingers_up_history), key=fingers_up_history.count))
                    
                    # Tampilkan jumlah jari
                    cv2.putText(frame, f'Jari: {smoothed_fingers}', (20, 80), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                    
                    # Kontrol presentasi
                    current_time = time.time()
                    if current_time - last_gesture_time > gesture_cooldown:
                        if smoothed_fingers == 2:
                            pyautogui.press('right')  # Slide berikutnya
                            cv2.putText(frame, "Slide Berikutnya", (20, 110), 
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                            globals()['last_gesture_time'] = current_time
                        elif smoothed_fingers == 3:
                            pyautogui.press('left')  # Slide sebelumnya
                            cv2.putText(frame, "Slide Sebelumnya", (20, 110), 
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                            globals()['last_gesture_time'] = current_time

                    # Gestur OK untuk mulai/berhenti
                    if detect_ok_gesture(hand_landmarks) and current_time - last_gesture_time > gesture_cooldown:
                        pyautogui.press('f5')  # Mulai/berhenti presentasi
                        cv2.putText(frame, "Presentasi Mulai/Berhenti", (20, 110), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                        globals()['last_gesture_time'] = current_time

                    # Gestur jempol untuk pointer
                    if detect_thumb_gesture(hand_landmarks):
                        if not pointer_active and current_time - last_gesture_time > gesture_cooldown:
                            pointer_active = True
                            globals()['last_gesture_time'] = current_time
                        if pointer_active:
                            x = int(hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP].x * frame.shape[1])
                            y = int(hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP].y * frame.shape[0])
                            cv2.circle(frame, (x, y), 10, (0, 0, 255), -1)  # Pointer merah
                            pyautogui.moveTo(x * 2, y * 2)  # Skala ke layar
                            cv2.putText(frame, "Pointer Aktif", (20, 110), 
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                    else:
                        if pointer_active and current_time - last_gesture_time > gesture_cooldown:
                            pointer_active = False
                            globals()['last_gesture_time'] = current_time

            # Tampilkan frame
            cv2.imshow('GestureSlide', frame)

            # Tekan 'q' untuk keluar
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except Exception as e:
        print(f"Terjadi kesalahan: {e}")
    
    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()