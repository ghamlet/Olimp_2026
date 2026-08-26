import cv2
import os
from datetime import datetime
from pathlib import Path

""" Простая запись видео с камеры без управления роботом.
    Файлы сохраняются в папку records с уникальным именем.
    Запуск: python3 record_camera.py
    Остановка: клавиша ESC/q в окне предпросмотра или Ctrl+C в терминале.
    Без дисплея (SSH) окно предпросмотра не открывается, остановка - Ctrl+C.
"""

CAMERA_ID = '/dev/video0'
RECORD_FPS = 30.0  # частота кадров записи видео
RECORDS_DIR = Path(__file__).resolve().parent / 'records'  # папка для сохранения видеозаписей
SHOW_PREVIEW = bool(os.environ.get('DISPLAY'))  # окно предпросмотра только при наличии дисплея

# настраиваем камеру
cap = cv2.VideoCapture(CAMERA_ID, cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 960)

if not cap.isOpened():
    print('[ERROR] Cannot open camera ID:', CAMERA_ID)
    quit()

# пропускаем часть кадров, для стабилизации настроек камеры
for i in range(30):
    ret, frame = cap.read()

# готовим файл записи с уникальным именем run_ГГГГММДД_ЧЧММСС.avi
RECORDS_DIR.mkdir(parents=True, exist_ok=True)
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
output_file = RECORDS_DIR / f'cam_{timestamp}.avi'
h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
writer = cv2.VideoWriter(str(output_file), cv2.VideoWriter_fourcc(*'MJPG'), RECORD_FPS, (w, h))
if not writer.isOpened():
    print('[ERROR] Cannot open video writer:', output_file)
    cap.release()
    quit()

print(f'[INFO] Запись видео: {output_file} ({w}x{h} @ {RECORD_FPS:.0f} fps)')
print('[INFO] Остановка: ESC/q в окне предпросмотра или Ctrl+C')

frame_count = 0
try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print('[ERROR] Не удалось прочитать кадр, запись остановлена')
            break

        writer.write(frame)
        frame_count += 1

        # окно предпросмотра, чтобы видеть, что пишется
        if SHOW_PREVIEW:
            cv2.imshow('Recording (ESC to stop)', frame)
            if cv2.waitKey(1) & 0xFF in (27, ord('q')):
                print('[INFO] Остановлено пользователем')
                break
except KeyboardInterrupt:
    print('\n[INFO] Остановлено пользователем')
finally:
    print(f'[INFO] Записано кадров: {frame_count}, файл: {output_file}')
    writer.release()  # закрываем файл, чтобы он корректно сохранился
    cap.release()
    cv2.destroyAllWindows()
