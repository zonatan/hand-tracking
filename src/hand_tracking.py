import cv2
import mediapipe as mp
import numpy as np
from collections import deque

# Inisialisasi MediaPipe Hands dengan parameter yang lebih ketat
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.85, min_tracking_confidence=0.85)

# Fungsi untuk menemukan indeks webcam yang valid
def find_webcam():
    for i in range(3):  # Coba indeks 0, 1, 2
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            print(f"Webcam ditemukan pada indeks {i}")
            return cap, i
        cap.release()
    return None, None

# Inisialisasi webcam
cap, index = find_webcam()
if cap is None:
    print("Error: Tidak ada webcam yang ditemukan. Pastikan webcam terhubung dan tidak digunakan aplikasi lain.")
    exit()

def is_hand_upright(hand_landmarks):
    """Cek apakah tangan dalam posisi tegak (jari menunjuk ke atas)."""
    wrist = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]
    middle_finger_mcp = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_MCP]
    return wrist.y > middle_finger_mcp.y  # Tangan tegak jika pergelangan tangan di bawah MCP

def count_fingers(hand_landmarks, frame):
    """Menghitung jumlah jari yang terangkat dengan logika yang lebih akurat."""
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
    for tip, pip, mcp in zip(finger_tips, finger_pip, finger_mcp):
        tip_y = hand_landmarks.landmark[tip].y
        pip_y = hand_landmarks.landmark[pip].y
        mcp_y = hand_landmarks.landmark[mcp].y
        # Jari dianggap terangkat jika ujung jari lebih tinggi dari PIP dan MCP
        if is_hand_upright(hand_landmarks):
            if tip_y < pip_y - 0.03 and tip_y < mcp_y - 0.03:  # Ambang batas ketat
                fingers_up += 1
                # Tandai ujung jari yang terdeteksi dengan lingkaran hijau
                x = int(hand_landmarks.landmark[tip].x * frame.shape[1])
                y = int(hand_landmarks.landmark[tip].y * frame.shape[0])
                cv2.circle(frame, (x, y), 8, (0, 255, 0), -1)
        else:
            # Jika tangan terbalik, balik logika perbandingan
            if tip_y > pip_y + 0.03 and tip_y > mcp_y + 0.03:
                fingers_up += 1
                x = int(hand_landmarks.landmark[tip].x * frame.shape[1])
                y = int(hand_landmarks.landmark[tip].y * frame.shape[0])
                cv2.circle(frame, (x, y), 8, (0, 255, 0), -1)
    
    return fingers_up

def detect_ok_gesture(hand_landmarks):
    """Mendeteksi gestur OK (jempol dan telunjuk membentuk lingkaran)."""
    thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
    index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
    distance = np.sqrt((thumb_tip.x - index_tip.x)**2 + (thumb_tip.y - index_tip.y)**2)
    return distance < 0.05

def main():
    try:
        # Kurangi resolusi untuk performa lebih baik
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        # Buffer untuk smoothing jumlah jari
        fingers_up_history = deque(maxlen=5)

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                print("Gagal menangkap frame dari webcam.")
                break

            # Konversi frame ke RGB untuk MediaPipe
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(frame_rgb)

            # Gambar landmark tangan dan hitung jari
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                    
                    # Hitung jari yang terangkat
                    fingers_up = count_fingers(hand_landmarks, frame)
                    fingers_up_history.append(fingers_up)
                    
                    # Gunakan mayoritas dari 5 frame terakhir untuk stabilitas
                    if fingers_up_history:
                        fingers_up = max(set(fingers_up_history), key=fingers_up_history.count)
                    
                    cv2.putText(frame, f'Jari Terangkat: {fingers_up}', (50, 50), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    
                    # Deteksi gestur jempol
                    thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
                    thumb_ip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_IP]
                    if is_hand_upright(hand_landmarks):
                        if thumb_tip.y < thumb_ip.y - 0.03:
                            cv2.putText(frame, "Jempol Terangkat!", (50, 100), 
                                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    else:
                        if thumb_tip.y > thumb_ip.y + 0.03:
                            cv2.putText(frame, "Jempol Terangkat!", (50, 100), 
                                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    
                    # Deteksi gestur OK
                    if detect_ok_gesture(hand_landmarks):
                        cv2.putText(frame, "Gestur OK Terdeteksi!", (50, 150), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            # Tampilkan frame
            cv2.imshow('Hand Tracking', frame)

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