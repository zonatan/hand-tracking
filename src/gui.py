import tkinter as tk
from PIL import Image, ImageTk
import queue
import threading
from hand_tracking import gesture_queue, calibration_mode, calibration_threshold, start_processing, running
import os

class GestureSlideGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("GestureSlide Pro")
        self.root.geometry("700x500")
        self.root.configure(bg="#1e1e2e")
        
        # Gaya modern
        self.root.option_add("*Font", "Helvetica 12")
        self.root.option_add("*Button.Background", "#3b3b4b")
        self.root.option_add("*Button.Foreground", "white")
        self.root.option_add("*Button.ActiveBackground", "#4b4b5b")
        self.root.option_add("*Label.Background", "#1e1e2e")
        self.root.option_add("*Label.Foreground", "white")
        
        # Ikon gestur (menggunakan emoji sebagai placeholder)
        self.gesture_icons = {
            "Slide Berikutnya": ("➡️", "#00ff00"),
            "Slide Sebelumnya": ("⬅️", "#ffaa00"),
            "Zoom In": ("+", "#ff0000"),
            "Zoom Out": ("−", "#ff00ff"),
            "Presentasi Mulai/Berhenti": ("OK", "#00ffff"),
            "Pointer Aktif": ("P", "#ff3232"),
            "Pointer Nonaktif": ("P", "#ff3232"),
            "Tidak Ada Gestur": ("", "#1e1e2e")
        }
        
        # Animasi fade
        self.status_opacity = 1.0
        self.fade_direction = -0.05
        
        # UI Elements
        self.title_label = tk.Label(root, text="GestureSlide Pro", font=("Helvetica", 24, "bold"), bg="#1e1e2e", fg="#00ffcc")
        self.title_label.pack(pady=15)
        
        self.status_frame = tk.Frame(root, bg="#1e1e2e")
        self.status_frame.pack(pady=10)
        self.status_label = tk.Label(self.status_frame, text="Status: Tidak Ada Gestur", font=("Helvetica", 16), bg="#1e1e2e")
        self.status_label.pack()
        
        self.icon_label = tk.Label(root, text="", font=("Helvetica", 40), bg="#1e1e2e")
        self.icon_label.pack(pady=15)
        
        self.info_frame = tk.Frame(root, bg="#1e1e2e")
        self.info_frame.pack(pady=10)
        self.fingers_label = tk.Label(self.info_frame, text="Jari: 0", font=("Helvetica", 12))
        self.fingers_label.pack(side=tk.LEFT, padx=10)
        self.mode_label = tk.Label(self.info_frame, text="Mode: Presentasi", font=("Helvetica", 12))
        self.mode_label.pack(side=tk.LEFT, padx=10)
        self.threshold_label = tk.Label(self.info_frame, text=f"Ambang: {calibration_threshold:.3f}", font=("Helvetica", 12))
        self.threshold_label.pack(side=tk.LEFT, padx=10)
        
        self.debug_label = tk.Label(root, text="Debug: Menunggu gestur...", font=("Helvetica", 10), fg="#aaaaaa", bg="#1e1e2e")
        self.debug_label.pack(pady=5)
        
        # Tombol kontrol
        self.button_frame = tk.Frame(root, bg="#1e1e2e")
        self.button_frame.pack(pady=15)
        
        self.calibrate_button = tk.Button(self.button_frame, text="Kalibrasi (C)", command=self.toggle_calibration, width=12)
        self.calibrate_button.pack(side=tk.LEFT, padx=5)
        
        self.inc_threshold_button = tk.Button(self.button_frame, text="+", command=self.increase_threshold, width=5, state=tk.DISABLED)
        self.inc_threshold_button.pack(side=tk.LEFT, padx=5)
        
        self.dec_threshold_button = tk.Button(self.button_frame, text="-", command=self.decrease_threshold, width=5, state=tk.DISABLED)
        self.dec_threshold_button.pack(side=tk.LEFT, padx=5)
        
        self.exit_button = tk.Button(self.button_frame, text="Keluar (Q)", command=self.exit, width=12)
        self.exit_button.pack(side=tk.LEFT, padx=5)
        
        # Petunjuk gestur
        self.guide_frame = tk.Frame(root, bg="#1e1e2e")
        self.guide_frame.pack(pady=10)
        for gesture, (icon, color) in self.gesture_icons.items():
            if gesture != "Tidak Ada Gestur" and gesture != "Pointer Nonaktif":
                tk.Label(self.guide_frame, text=f"{gesture}: {icon}", font=("Helvetica", 10), fg=color, bg="#1e1e2e").pack(anchor="w")
        
        # Bind keyboard
        self.root.bind('<c>', lambda event: self.toggle_calibration())
        self.root.bind('<plus>', lambda event: self.increase_threshold())
        self.root.bind('<minus>', lambda event: self.decrease_threshold())
        self.root.bind('<q>', lambda event: self.exit())
        
        # Mulai pemrosesan gestur
        start_processing()
        
        # Update UI
        self.update_ui()
    
    def toggle_calibration(self):
        global calibration_mode
        calibration_mode = not calibration_mode
        self.mode_label.config(text=f"Mode: {'Kalibrasi' if calibration_mode else 'Presentasi'}")
        self.inc_threshold_button.config(state=tk.NORMAL if calibration_mode else tk.DISABLED)
        self.dec_threshold_button.config(state=tk.NORMAL if calibration_mode else tk.DISABLED)
        self.debug_label.config(text=f"Debug: Mode {'Kalibrasi' if calibration_mode else 'Presentasi'} diaktifkan")
    
    def increase_threshold(self):
        global calibration_threshold
        calibration_threshold += 0.005
        self.threshold_label.config(text=f"Ambang: {calibration_threshold:.3f}")
        self.debug_label.config(text=f"Debug: Ambang meningkat ke {calibration_threshold:.3f}")
    
    def decrease_threshold(self):
        global calibration_threshold
        calibration_threshold = max(0.01, calibration_threshold - 0.005)
        self.threshold_label.config(text=f"Ambang: {calibration_threshold:.3f}")
        self.debug_label.config(text=f"Debug: Ambang menurun ke {calibration_threshold:.3f}")
    
    def exit(self):
        global running
        running = False
        self.root.quit()
    
    def update_ui(self):
        try:
            _, gesture_data = gesture_queue.get_nowait()
            status = gesture_data["status"]
            fingers = gesture_data["smoothed_fingers"]
            icon, color = self.gesture_icons.get(status, ("", "#1e1e2e"))
            
            # Animasi fade
            if status != "Tidak Ada Gestur":
                self.status_opacity += self.fade_direction
                if self.status_opacity <= 0.3 or self.status_opacity >= 1.0:
                    self.fade_direction = -self.fade_direction
                self.status_label.config(text=f"Status: {status}", fg=f"#{int(255 * self.status_opacity):02x}{int(255 * self.status_opacity):02x}{int(255 * self.status_opacity):02x}")
            else:
                self.status_label.config(text=f"Status: {status}", fg="white")
                self.status_opacity = 1.0
                self.fade_direction = -0.05
            
            self.icon_label.config(text=icon, bg=color)
            self.fingers_label.config(text=f"Jari: {fingers}")
            self.threshold_label.config(text=f"Ambang: {calibration_threshold:.3f}")
            self.debug_label.config(text=f"Debug: Gestur {status} terdeteksi, Jari: {fingers}")
        except queue.Empty:
            pass
        self.root.after(30, self.update_ui)

def main():
    root = tk.Tk()
    app = GestureSlideGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()