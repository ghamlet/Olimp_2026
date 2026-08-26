import argparse
import atexit
import queue
import time
import random
import threading
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

from Arduino_A26 import Arduino
from road_utils import *

""" Запускать на бортовом компьютере беспилотника.
    Рядом должны быть Arduino_A26.py и road_utils.py.

    Аналог StadionRunner.py, но каждый заезд записывается в видео:
    файлы складываются в папку records рядом со скриптом,
    имя файла уникально благодаря дате и времени запуска записи.

    Беспилотник движется по дорожной разметке:
    поиск линий дорожной разметки,
    определение угла поворота колёс для движения к центру полосы,
    выбор скорости по зоне угла (прямая/поворот),
    отправка команд микроконтроллеру.
"""

BASE_SPEED = 1560    # базовая скорость движения по прямой линии
TURN_SPEED = 1565          # скорость в поворотах, когда колёса вывернуты за пределы зоны прямой
ANGLE_TOLERANCE = 20  # допуск зоны прямой: |angle - 90| <= ANGLE_TOLERANCE
THRESHOLD = 250  # порог бинаризации для поиска линий разметки
CAMERA_ID = '/dev/video0'
# ARDUINO_PORT = 'COM3'
# ARDUINO_PORT = '/dev/ttyS0'
ARDUINO_PORT = '/dev/ttyUSB0'

RECORDS_DIR = Path(__file__).resolve().parent / 'records'  # папка для сохранения видеозаписей
RECORD_FPS = 30.0  # частота кадров записи видео

parser = argparse.ArgumentParser(description='StadionRunner с записью видео')
parser.add_argument('--name', type=str, default=None,
                    help='Имя файла для записи видео (без расширения). Если не задано — автоматически по дате/времени.')
args = parser.parse_args()
VIDEO_NAME = args.name

GO = 'GO'
STOP = 'STOP'

STATE = GO
PREV_STATE = None
PREV_SUBSTATE = None
SUBSTATE = None


arduino = None
video_writer = None


@atexit.register
def exit_func(*args):
    if arduino is not None:
        arduino.close()
    if video_writer is not None:
        video_writer.close()  # дописываем буфер кадров и корректно закрываем видеофайл


arduino = Arduino(ARDUINO_PORT)
print("Arduino connected")




class AsyncVideoWriter:
    """Пишет кадры в файл из фонового потока.
    Кодирование видео занимает десятки миллисекунд на кадр, если делать это в основном
    цикле, частота управления падает и беспилотник начинает ехать хуже.
    Поэтому основной цикл только кладёт кадр в очередь и сразу идёт дальше."""

    def __init__(self, output_file, fps, frame_size):
        self.tasks = queue.Queue(maxsize=90)  # буфер кадров на случай подтормаживаний диска
        self.dropped = 0  # сколько кадров выброшено из-за переполнения буфера
        self.writer = cv2.VideoWriter(str(output_file), cv2.VideoWriter_fourcc(*'MJPG'), fps, frame_size)
        if not self.writer.isOpened():
            print('[ERROR] Cannot open video writer:', output_file)
            quit()
        self.worker = threading.Thread(target=self._work, daemon=True)
        self.worker.start()

    def _work(self):
        while True:
            frame = self.tasks.get()
            if frame is None:  # сигнал завершения работы
                break
            self.writer.write(frame)  # медленная операция - выполняется здесь, вне цикла управления

    def write(self, frame):
        try:
            self.tasks.put_nowait(frame)  # никогда не ждём: лучше потерять кадр, чем задержать управление
        except queue.Full:
            self.dropped += 1

    def close(self):
        self.tasks.put(None)  # останавливаем фоновый поток после дописывания всех кадров
        self.worker.join(timeout=5)
        self.writer.release()
        if self.dropped:
            print(f'[INFO] При записи пропущено кадров: {self.dropped}')


def open_video_writer(frame_shape):
    """Открывает новый файл записи.
    Если VIDEO_NAME задан — имя файла берётся из него, иначе — автоматически run_ГГГГММДД_ЧЧММСС."""
    RECORDS_DIR.mkdir(parents=True, exist_ok=True)
    if VIDEO_NAME:
        filename = f'{VIDEO_NAME}.avi'
    else:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'run_{timestamp}.avi'
    output_file = RECORDS_DIR / filename
    h, w = frame_shape[:2]
    print(f'[INFO] Запись видео: {output_file}')
    return AsyncVideoWriter(output_file, RECORD_FPS, (w, h))


# настраиваем камеру
cap = cv2.VideoCapture(CAMERA_ID, cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 960)

if not cap.isOpened():
    print('[ERROR] Cannot open camera ID:', CAMERA_ID)
    quit()

find_lines = centre_mass2 # название функции для поиска линий разметки

# пропускаем часть кадров, для стабилизации настроек камеры
for i in range(30):
    ret, frame = cap.read()

last_err = 0
ped_log_state_prev = None
last_ped = 0
while True:
    start_time = time.time()
    ret, frame = cap.read()
    end_frame = time.time()
    if not ret:
        break

    frame = frame[-720:, :]  # для поиска разметки весь кадр не нужен
    orig_frame = frame.copy()

    # Запись видео: при первом кадре открываем файл, дальше пишем в него каждый кадр
    if video_writer is None:
        video_writer = open_video_writer(orig_frame.shape)
    video_writer.write(orig_frame)

    frame = cv2.resize(orig_frame, SIZE)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # Переводим изображение в чёрно-белое с градациями серого
    bin = cv2.inRange(gray, THRESHOLD, 255)  # Бинаризуем по порогу, должны остаться только белые линии разметки
    # bin = binarize(frame, THRESHOLD)

    wrapped = trans_perspective(bin, TRAP, RECT, SIZE)  # получаем область перед колёсами
    left, right = find_lines(wrapped)  # координаты левой и правой линий разметки

    # ПИД-регулятор для определения угла поворота колёс
    # ПИД старается удерживать центр кадра ровно между линиями дорожной разметки
    err = 0 - ((left + right) // 2 - wrapped.shape[1] // 2)

    # err = -err  # Инвертирование направления поворота колёс  На наших айкарах не надо

    angle = int(90 + KP * err + KD * (err - last_err))  # серва на роботе зеркальная: поправка входит с обратным знаком
    last_err = err

    angle = min(max(45, angle), 135)
    print(angle)


    if PREV_STATE != STATE:
        print(f'STATE: {STATE}')
        PREV_STATE = STATE

    if STATE != STOP:
        # Выбор скорости: в зоне прямой (90 ± ANGLE_TOLERANCE) едем на базовой скорости,
        # при вывороте колёс за пределы зоны - замедляемся для прохождения поворота
        if abs(angle - 90) <= ANGLE_TOLERANCE:
            arduino.set_speed(BASE_SPEED)
        else:
            arduino.set_speed(TURN_SPEED)
        arduino.set_angle(angle)
    else:
        arduino.set_speed(1500)  # Стоп-сигнал
        # arduino.stop()  # Ардуино подтвердит получение

    end_time = time.time()

    fps = 1 / (end_time - start_time)
    if fps < 10:
        print(f'[WARNING] FPS is too low! ({fps:.1f} fps)')
