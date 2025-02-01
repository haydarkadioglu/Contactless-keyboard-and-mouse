import cv2
import numpy as np
from ultralytics import YOLO
import time
import win32gui
import win32con
import ctypes
import pyautogui


class AppWindow:
    def __init__(self, window_name, target_width, target_height):
        self.window_name = window_name
        self.target_width = target_width
        self.target_height = target_height
        self.dragging = False
        self.prev_mouse_pos = (0, 0)

        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, self.target_width, self.target_height)
        self.hwnd = win32gui.FindWindow(None, self.window_name)

        self._configure_window()
        self._enable_dragging()

    def _configure_window(self):
        style = win32gui.GetWindowLong(self.hwnd, win32con.GWL_STYLE)
        style &= ~win32con.WS_OVERLAPPEDWINDOW
        win32gui.SetWindowLong(self.hwnd, win32con.GWL_STYLE, style)
        win32gui.SetWindowPos(self.hwnd, win32con.HWND_TOPMOST, 0, 0, self.target_width, self.target_height, win32con.SWP_FRAMECHANGED)

        extended_style = win32gui.GetWindowLong(self.hwnd, win32con.GWL_EXSTYLE)
        win32gui.SetWindowLong(self.hwnd, win32con.GWL_EXSTYLE, extended_style | win32con.WS_EX_LAYERED)
        ctypes.windll.user32.SetLayeredWindowAttributes(self.hwnd, 0, 200, win32con.LWA_ALPHA)

    def _enable_dragging(self):
        def mouse_callback(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN:
                self.dragging = True
                self.prev_mouse_pos = (x, y)
            elif event == cv2.EVENT_MOUSEMOVE and self.dragging:
                dx = x - self.prev_mouse_pos[0]
                dy = y - self.prev_mouse_pos[1]
                rect = win32gui.GetWindowRect(self.hwnd)
                new_x = rect[0] + dx
                new_y = rect[1] + dy
                win32gui.SetWindowPos(self.hwnd, None, new_x, new_y, 0, 0, win32con.SWP_NOSIZE | win32con.SWP_NOZORDER)
                self.prev_mouse_pos = (x, y)
            elif event == cv2.EVENT_LBUTTONUP:
                self.dragging = False

        cv2.setMouseCallback(self.window_name, mouse_callback)


confidence_score = 0.6
font = cv2.FONT_HERSHEY_SIMPLEX
model_path = "../weights/YoloLargeBest.pt"
model = YOLO(model_path)
labels = model.names

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

app_window = AppWindow("Tahmin Penceresi", 150, 150)

frame_skip = 5
frame_counter = 0
last_prediction = ""

while True:
    ret, frame = cap.read()
    if not ret:
        print("[ERROR] Kameradan görüntü alınamıyor!")
        break

    if frame_counter % frame_skip == 0:
        results = model(frame, verbose=False, conf=confidence_score, iou=0.5)[0]
        boxes = np.array(results.boxes.data.tolist())

        prediction_text = ""

        for box in boxes:
            x1, y1, x2, y2, score, class_id = box
            x1, y1, x2, y2, class_id = int(x1), int(y1), int(x2), int(y2), int(class_id)

            if score > confidence_score:
                class_name = results.names[class_id]
                prediction_text = f"{class_name}"
                break  # İlk tahmini al ve çık

        # Print prediction in new window
        blank_image = np.zeros((150, 150, 3), dtype=np.uint8)
        if prediction_text and prediction_text != last_prediction:
            text_size = cv2.getTextSize(prediction_text, font, 0.8, 2)[0]
            text_x = (blank_image.shape[1] - text_size[0]) // 2
            text_y = (blank_image.shape[0] + text_size[1]) // 2
            cv2.putText(blank_image, prediction_text, (text_x, text_y), font, 0.8, (255, 255, 255), 2)

            # If you want to write a post, do not comment this line.
#            time.sleep(1)
#            pyautogui.typewrite(prediction_text)
#            last_prediction = prediction_text

        cv2.imshow("Tahmin Penceresi", blank_image)

    frame_counter += 1

    if cv2.waitKey(20) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
