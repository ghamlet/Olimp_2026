# -*- coding: utf-8 -*-
import cv2
import numpy as np
import math

# Не используется
def load_tools():
    tools = []
    return tools


def intersection_number(img):
    # Если хотя бы один из пикселей, соответствующих перекрёстку не чёрный, то
    # записываем номер перекрёстка в список.
    if (np.any(img[95, 360] != [0, 0, 0]) or
        np.any(img[160, 465] != [0, 0, 0]) or
        np.any(img[55, 520] != [0, 0, 0])):
        return 1

    if (np.any(img[340, 48] != [0, 0, 0]) or
        np.any(img[400, 140] != [0, 0, 0]) or
        np.any(img[500, 90] != [0, 0, 0])):
        return 2

    if (np.any(img[340, 795] != [0, 0, 0]) or
        np.any(img[500, 830] != [0, 0, 0]) or
        np.any(img[440, 735] != [0, 0, 0])):
        return 4

    if (np.any(img[790, 355] != [0, 0, 0]) or
        np.any(img[690, 420] != [0, 0, 0]) or
        np.any(img[750, 525] != [0, 0, 0])):
        return 5

    if (np.any(img[445, 355] != [0, 0, 0]) or
        np.any(img[510, 460] != [0, 0, 0]) or
        np.any(img[340, 420] != [0, 0, 0]) or
        np.any(img[405, 525] != [0, 0, 0])):
        return 3
    return 0


def creating_graph(crossroad):
    # Создаём матрицу 5х5, заполненную нулями.
    result = np.zeros((5, 5), dtype=np.int8)

    # Перебираем все посещённые перекрёстки, кроме последнего.
    for n, i in enumerate(crossroad[:-1]):
        # n+1 - номер следующего посещённого перекрёстка.
        # crossroad[n + 1] - 1  - индекс в матрице, следующего посещённого перекрёстка
        # [i - 1] - индекс в матрице, текущего посещённого перекрётска
        result[i - 1][crossroad[n + 1] - 1] += 1
    return result


# Основная функция
def track_movement(video, tools) -> int:
    """ Функция для отслеживания маршрута автомобился.
        Входные данные: видео-объект (cv2.VideoCapture)
        Выходные данные: матрицу смежности графа в виде numpy массива (dtype=np.uint8)
        Примеры вывода:
            [[0, 0, 0, 1, 0], [0, 0, 1, 0, 0], [1, 0, 0, 0, 0], [0, 0, 1, 0, 0], [0, 0, 0, 0, 0]]
    """

    crossroad = [0]  # Список посещённых перекрёстков.
    # Ядро свёртки для операции заполнения внутренних пустот на чёрно-белом изображении
    st1 = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))

    while True:  # Цикл чтения кадров.
        ret_val, img = video.read()
        if not ret_val:
            break  # Выходим из цикла, если кадры закончились.

        # Для удобства бинаризации, переводим изображение в формат HSV
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        # Бинаризуем изображение так, чтобы белыми остались только пиксели автомобиля
        maks_e = cv2.inRange(hsv, (10, 100, 100), (56, 246, 255))
        cv2.imshow("mask_e_1", maks_e)
        # Заполняем тёмные промежутки, внутри чёрно-белого изображения автомобиля
        img_car = cv2.morphologyEx(maks_e, cv2.MORPH_CLOSE, st1, iterations=3)
        cv2.imshow("img_car", img_car)

        # Проверяем не проехала ли машина, по какому то из перекрёстков.
        # Запоминаем значение последнего посещённого перекрёстка.
        # Добавляем значение в список только тогда, когда оно не совпадает с ранее записанным.
        # Т.е. при первом посещении нового перекрёстка.
        old = intersection_number(img_car)
        if crossroad[-1] != old and old:
            crossroad.append(old)

    # Заполняем матрицу посещений рёбер графа.
    # Первый элемент списка - 0, не учитываем.
    result = creating_graph(crossroad[1:])
    return result
