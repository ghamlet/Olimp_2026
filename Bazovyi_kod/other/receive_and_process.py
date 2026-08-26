import atexit
import sys
import time
import random
import threading
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent / 'streaming'))
from streaming.receive_and_record import DEFAULT_URL, stream_frames

from road_utils import *

""" Запускать на ПК.
    На роботе должен быть запущен streaming/stream_simple.py.

    Прямая копия StadionRunner.py: беспилотник движется по дорожной разметке,
    поиск линий дорожной разметки и определение угла поворота колёс для движения
    к центру полосы — всё как в оригинале, но кадры берутся из MJPEG-потока
    робота, без ардуино и руления колёс.
"""

CAR_SPEED = 1580  # скорость беспилотника
THRESHOLD = 250  # порог бинаризации для поиска линий разметки

GO = 'GO'
STOP = 'STOP'

STATE = GO
PREV_STATE = None
PREV_SUBSTATE = None
SUBSTATE = None

find_lines = centre_mass2 # название функции для поиска линий разметки

last_err = 0
ped_log_state_prev = None
last_ped = 0
frames = stream_frames(DEFAULT_URL)

# пропускаем часть кадров, для стабилизации настроек камеры
for i in range(30):
    next(frames)

while True:
    start_time = time.time()
    frame = next(frames)
    end_frame = time.time()

    frame = frame[-720:, :]  # для поиска разметки весь кадр не нужен
    orig_frame = frame.copy()
    cv2.imshow("orig_frame", orig_frame)
    frame = cv2.resize(frame, SIZE)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # Переводим изображение в чёрно-белое с градациями серого
    bin = cv2.inRange(gray, THRESHOLD, 255)  # Бинаризуем по порогу, должны остаться только белые линии разметки
    # bin = binarize(frame, THRESHOLD)
    cv2.imshow("bin",bin)


    cv2.waitKey(1)

    wrapped = trans_perspective(bin, TRAP, RECT, SIZE, d=1)  # получаем область перед колёсами

    left, right = find_lines(wrapped, d=1)  # координаты левой и правой линий разметки


    # ПИД-регулятор для определения угла поворота колёс
    # ПИД старается удерживать центр кадра ровно между линиями дорожной разметки
    err = 0 - ((left + right) // 2 - wrapped.shape[1] // 2)
    #err = -err  # Инвертирование направления поворота колёс
    angle = int(90 + KP * err + KD * (err - last_err))  # высчитываем угол
    last_err = err

    angle = min(max(45, angle), 135)

    if PREV_STATE != STATE:
        print(f'STATE: {STATE})')
        PREV_STATE = STATE

    end_time = time.time()

    fps = 1 / (end_time - start_time)
    # if fps < 10:
    #     print(f'[WARNING] FPS is too low! ({fps:.1f} fps)')
