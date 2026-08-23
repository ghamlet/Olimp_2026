# -*- coding: utf-8 -*-
import cv2
import numpy as np


def find_black_objects(image):
    """Находит черные объекты (перекрестки) на изображении."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY_INV)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    result = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 100:
            continue

        x, y, w, h = cv2.boundingRect(cnt)
        center_x = x + w // 2
        center_y = y + h // 2
        result.append((center_x, center_y))

    return result


def sort_tuples_by_first_element(tuple_list):
    """Сортирует перекрестки слева направо по X и назначает ID (1, 2, 3...)."""
    sorted_data = sorted(tuple_list, key=lambda item: item[0])
    return [(i + 1, x, y) for i, (x, y) in enumerate(sorted_data)]


def get_all_pairs(sorted_points):
    """Генерирует все возможные пары перекрестков."""
    pairs = []
    n = len(sorted_points)
    for i in range(n):
        for j in range(i + 1, n):
            pairs.append((sorted_points[i], sorted_points[j]))
    return pairs


def find_colored_objects(image):
    """Находит цветные участки дорог в формате HSV."""
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    color_ranges = {
        "red": [
            (np.array([0, 100, 100]), np.array([10, 255, 255])),
            (np.array([160, 100, 100]), np.array([179, 255, 255]))
        ],
        "yellow": [
            (np.array([20, 100, 100]), np.array([35, 255, 255]))
        ],
        "green": [
            (np.array([40, 100, 100]), np.array([85, 255, 255]))
        ]
    }

    result = []
    for color_name, ranges in color_ranges.items():
        mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
        for lower, upper in ranges:
            mask = cv2.bitwise_or(mask, cv2.inRange(hsv, lower, upper))

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for cnt in contours:
            if cv2.contourArea(cnt) < 50:
                continue

            x, y, w, h = cv2.boundingRect(cnt)
            center_x = x + w // 2
            center_y = y + h // 2
            result.append([color_name, (center_x, center_y)])

    return result


def build_road_graph(all_pairs, colored_objects):
    """Связывает найденные перекрестки и участки в итоговый граф."""
    color_code = {"green": 1, "yellow": 2, "red": 3}
    
    result = {}
    for node1, node2 in all_pairs:
        result[node1[0]] = []
        result[node2[0]] = []

    for (id1, x1, y1), (id2, x2, y2) in all_pairs:
        found_colors = []

        for color_name, (cx, cy) in colored_objects:
            # Проверяем, находится ли точка в прямоугольной области между узлами
            if (min(x1, x2)  <= cx <= max(x1, x2) ) and \
               (min(y1, y2)  <= cy <= max(y1, y2) ):
                
                d1 = np.hypot(cx - x1, cy - y1)
                d2 = np.hypot(cx - x2, cy - y2)
                d_total = np.hypot(x2 - x1, y2 - y1)
                
                # Проверка принадлежности точки прямой линии
                if abs((d1 + d2) - d_total) < 0.01:
                    found_colors.append((d1, color_code[color_name]))

        if found_colors:
            found_colors.sort(key=lambda item: item[0])
            
            road_from_1 = [c[1] for c in found_colors]
            road_from_2 = road_from_1[::-1]
            
            result[id1].append(road_from_1)
            result[id2].append(road_from_2)

    return {str(k): v for k, v in sorted(result.items())}





def analyze_traffic(image) -> dict:
    """Главная функция решения задачи."""
    if image is None:
        return {}

    # 1. Поиск центров перекрестков
    centers = find_black_objects(image)
    if not centers:
        return {}

    # 2. Нумерация перекрестков слева направо
    sorted_centers = sort_tuples_by_first_element(centers)

    # 3. Генерация пар перекрестков
    all_pairs = get_all_pairs(sorted_centers)

    # 4. Поиск всех цветных кусочков
    colored_objects = find_colored_objects(image)

    # 5. Составление графа дорог
    result = build_road_graph(all_pairs, colored_objects)

    return result