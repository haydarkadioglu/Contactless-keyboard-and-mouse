import cv2
import mediapipe as mp
import pyautogui
import math
import numpy as np
import win32gui
import win32con
import ctypes
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.colorchooser import askcolor

# Mediapipe'in el izleme modülü
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

# Çizim renkleri için beyaz ayarı

landmark_drawing_spec = mp_draw.DrawingSpec(color=(255, 255, 255), thickness=2, circle_radius=2)
connection_drawing_spec = mp_draw.DrawingSpec(color=(255, 255, 255), thickness=2)

# Kamera açılır
cap = cv2.VideoCapture(0)

# Orijinal pencere boyutları
frame_width = 640
frame_height = 480

# İstenen pencere boyutları
target_width = 150
target_height = 150

# Pencere oluşturma
window_name = "Custom Window"
cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
cv2.resizeWindow(window_name, target_width, target_height)

# Pencereyi başlıksız ve kenarlıksız yapmak
hwnd = win32gui.FindWindow(None, window_name)
style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
style &= ~win32con.WS_OVERLAPPEDWINDOW  # Kenarlıkları ve başlık çubuğunu kaldır
win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, style)

# Pencereyi sürekli en üstte tutmak için HWND_TOPMOST kullan
win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, target_width, target_height, win32con.SWP_FRAMECHANGED)

# Saydamlık eklemek için pencereye "layered" özelliği ekle
extended_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, extended_style | win32con.WS_EX_LAYERED)

# Saydamlık seviyesi ayarı (0: tamamen saydam, 255: tamamen opak)
opacity_level = 200  # %80 saydamlık (255 * 0.8)
ctypes.windll.user32.SetLayeredWindowAttributes(hwnd, 0, opacity_level, win32con.LWA_ALPHA)

# Fare sürükleme için gerekli değişkenler
dragging = False
prev_mouse_pos = (0, 0)

def opaklik_penceresi():
    def opaklik_degistir(value):
        label_deger.config(text=f"Seçilen Opaklık: {value}")

    def tamam():
        nonlocal secilen_deger
        secilen_deger = scale.get()
        opaklik_pencere.destroy()

    opaklik_pencere = tk.Toplevel()
    opaklik_pencere.title("Opaklık Ayarı")
    opaklik_pencere.geometry("300x200")

    secilen_deger = 0

    tk.Label(opaklik_pencere, text="Opaklık Ayarını Seçin (0-255):").pack(pady=10)

    scale = tk.Scale(opaklik_pencere, from_=0, to=255, orient="horizontal", command=opaklik_degistir)
    scale.pack(pady=5)

    label_deger = tk.Label(opaklik_pencere, text="Seçilen Opaklık: 0")
    label_deger.pack(pady=10)

    tk.Button(opaklik_pencere, text="Tamam", command=tamam).pack(pady=10)

    opaklik_pencere.wait_window()  # Pencere kapanana kadar bekle
    return secilen_deger

def renk_secici():
    color_code = askcolor(title="Bir renk seçin")
    if color_code[0]:  # Seçim yapılmışsa RGB değerlerini döndür
        return tuple(map(int, color_code[0]))  # Sadece RGB değerlerini döndür
    return None  # Seçim yapılmazsa None döndür

def secim_yonlendir():
    secilen_ayar = combobox_ayar.get()

    if secilen_ayar == "Opaklık Ayarı":
        secilen_opaklik = opaklik_penceresi()
        ctypes.windll.user32.SetLayeredWindowAttributes(hwnd, 0, secilen_opaklik, win32con.LWA_ALPHA)
    elif secilen_ayar == "Parmak Ucu Ayarı":
        renk = renk_secici()
        r, g, b = renk
        if renk:
            global landmark_drawing_spec, connection_drawing_spec
            landmark_drawing_spec = mp_draw.DrawingSpec(color=(b, g, r), thickness=2, circle_radius=2)


        else:
            messagebox.showwarning("Renk Seçimi", "Renk seçimi yapılmadı.")
    elif secilen_ayar == "Parmak Çizgisi Ayarı":
        renk = renk_secici()
        r, g, b = renk
        if renk:
            connection_drawing_spec = mp_draw.DrawingSpec(color=(b, g, r), thickness=2)
        else:
            messagebox.showwarning("Renk Seçimi", "Renk seçimi yapılmadı.")
    else:
        messagebox.showwarning("Hata", "Lütfen bir seçenek seçin.")


def pencere_ac():
    pencere = tk.Tk()
    pencere.title("Ayarlar Penceresi")
    pencere.geometry("300x200")

    # Tek bir Combobox
    label_ayar = tk.Label(pencere, text="Ayarlardan birini seçin:")
    label_ayar.pack(pady=10)

    global combobox_ayar
    combobox_ayar = ttk.Combobox(pencere, values=["Opaklık Ayarı", "Parmak Ucu Ayarı", "Parmak Çizgisi Ayarı"])
    combobox_ayar.set("Seçim yapın")  # Varsayılan değer
    combobox_ayar.pack(pady=5)

    # Seçim Butonu
    button_secim = tk.Button(pencere, text="Seçimi Onayla", command=secim_yonlendir)
    button_secim.pack(pady=20)

    pencere.mainloop()



# Fare olaylarını yönetme fonksiyonu
def mouse_callback(event, x, y, flags, param):
    global dragging, prev_mouse_pos, hwnd

    if event == cv2.EVENT_LBUTTONDOWN:  # Sol tuşa basıldı
        dragging = True
        prev_mouse_pos = (x, y)

    elif event == cv2.EVENT_MOUSEMOVE and dragging:  # Fare hareket ediyor
        curr_mouse_pos = (x, y)
        dx, dy = curr_mouse_pos[0] - prev_mouse_pos[0], curr_mouse_pos[1] - prev_mouse_pos[1]
        if dx != 0 or dy != 0:  # Hareket varsa
            rect = win32gui.GetWindowRect(hwnd)
            win32gui.SetWindowPos(hwnd, None, rect[0] + dx, rect[1] + dy, 0, 0,
                                  win32con.SWP_NOSIZE | win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE)
            prev_mouse_pos = curr_mouse_pos

    elif event == cv2.EVENT_LBUTTONUP:  # Sol tuş bırakıldı
        dragging = False


# OpenCV penceresi için fare olayları ayarla
cv2.setMouseCallback(window_name, mouse_callback)

# El hareketlerini ekranla uyumlu hale getirmek için ölçekleme faktörleri
scale_x = pyautogui.size().width / frame_width
scale_y = pyautogui.size().height / frame_height

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Kameradan alınan görüntüyü çevir ve RGB'ye dönüştür
    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Mediapipe ile el izleme
    result = hands.process(rgb_frame)

    # Siyah beyaz bir arka plan oluştur
    black_frame = np.zeros((frame_height, frame_width, 3), dtype=np.uint8)

    if result.multi_hand_landmarks and result.multi_handedness:
        for idx, hand_landmarks in enumerate(result.multi_hand_landmarks):
            hand_label = result.multi_handedness[idx].classification[0].label

            # İşaret parmağı ucu (8. landmark) ve başparmak ucu (4. landmark)
            index_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
            thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
            #mid_tip = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]

            # Kameradan alınan koordinatları, belirlenen çerçeveye göre al
            x_index = int(index_finger_tip.x * frame_width)
            y_index = int(index_finger_tip.y * frame_height)
            x_thumb = int(thumb_tip.x * frame_width)
            y_thumb = int(thumb_tip.y * frame_height)

            # İşaret parmağı ve başparmak arasındaki mesafeyi hesapla
            distance = math.hypot(x_thumb - x_index, y_thumb - y_index)

            if hand_label == "Right":  # Sağ el fare kontrolü yapar
                # Çerçeve koordinatlarını ekran boyutuna ölçekle
                mouse_x = int(x_index * scale_x)
                mouse_y = int(y_index * scale_y)

                # Fareyi ekran üzerinde hareket ettir
                pyautogui.moveTo(mouse_x, mouse_y)

                # Mesafe belirli bir eşikten küçükse tıklama yap
                if distance < 30:  # Eşik mesafesi
                    pyautogui.click()

            elif hand_label == "Left":  # Sol el sadece programı kapatır
                if distance < 30:  # Mesafe eşikten küçükse
                    #print("Sol el ile kapatma tespit edildi. Program kapatılıyor...")
                    #cap.release()
                    #cv2.destroyAllWindows()
                    #sys.exit()
                    pencere_ac()

            # Siyah arka plana el çizgilerini beyaz olarak çizin
            mp_draw.draw_landmarks(
                black_frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
                landmark_drawing_spec=landmark_drawing_spec,
                connection_drawing_spec=connection_drawing_spec
            )

    # Pencere boyutuna uygun hale getirmek için yeniden boyutlandır
    resized_black_frame = cv2.resize(black_frame, (target_width, target_height))
    cv2.imshow(window_name, resized_black_frame)

    if cv2.waitKey(1) & 0xFF == 27:  # ESC tuşu ile çıkış
        break

cap.release()
cv2.destroyAllWindows()
