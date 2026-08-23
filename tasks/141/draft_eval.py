import cv2
import numpy as np

def find_black_objects(image):
    """
    Находит черные объекты на изображении.
    Возвращает список кортежей (x, y) центров найденных объектов.
    """
   
    img_orig = image.copy()
    # 2. Преобразуем в оттенки серого
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 3. Создаем бинарную маску.
    # Порог 50 означает: все, что темнее 50 (из 255), считается черным.
    # Чем ниже порог, тем строже условие "черноты".
    # (Если фон тоже темный, порог нужно подбирать экспериментально)
    _, mask = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY_INV)

    # 4. Находим контуры объектов на маске
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    result = []
    
    # 5. Обрабатываем каждый найденный контур
    for cnt in contours:
        # Отбрасываем очень мелкие объекты (шум) или огромные объекты (весь фон), 
        # если они вдруг появились в маске.
        area = cv2.contourArea(cnt)
        if area < 100:  # Минимальная площадь пикселей (подбирается под размер точек)
            continue

        # Строим баундинг бокс (прямоугольник)
        x, y, w, h = cv2.boundingRect(cnt)

        cv2.rectangle(img_orig, (x, y), (x + w, y + h), (40, 40, 40), 2)


        # Вычисляем центр объекта (координаты x и y)
        center_x = x + w // 2
        center_y = y + h // 2

        # Добавляем кортеж (x, y) в итоговый массив
        result.append((center_x, center_y))

    cv2.imshow("img_orig", img_orig)
    cv2.waitKey(0)

    return result




def sort_tuples_by_first_element(tuple_list):
    
    # key=lambda x: x[0] означает: "сортируй по элементу с индексом 0 в каждом кортеже"
    sorted_data = sorted(tuple_list, key=lambda item: item[0])
    return [(i + 1, x, y) for i, (x, y) in enumerate(sorted_data)]  # добавить айдишники 




def get_all_pairs(sorted_points):
    pairs = []
    n = len(sorted_points)
    # Идем по индексам от 0 до конца
    for i in range(n):
        # Второй индекс всегда начинается со следующего за i (i+1), чтобы не было дублей (1,1) или (2,1)
        for j in range(i + 1, n):
            pairs.append((sorted_points[i], sorted_points[j]))
    return pairs





def find_colored_objects(image):
    """
    Находит объекты красного, желтого и зеленого цветов на изображении.
    Возвращает список: [ [цвет, (x, y)], ... ]
    """

    img_orig = image.copy()
    # Переводим в HSV (удобнее для работы с цветами)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)


    # Задаем диапазоны цветов в HSV (Hue: 0-179, Saturation: 0-255, Value: 0-255)
    # Красный цвет в OpenCV находится в двух диапазонах (в начале и в конце шкалы Hue)
    color_ranges = {
        "red": [
            (np.array([0, 100, 100]), np.array([10, 255, 255])),   # Красный (низкий Hue)
            (np.array([160, 100, 100]), np.array([179, 255, 255])) # Красный (высокий Hue)
        ],
        "yellow": [
            (np.array([20, 100, 100]), np.array([35, 255, 255]))
        ],
        "green": [
            (np.array([40, 100, 100]), np.array([85, 255, 255]))
        ]
    }

    result = []

    # Перебираем каждый цвет
    for color_name, ranges in color_ranges.items():
        # Создаем пустую маску для текущего цвета
        mask = np.zeros(hsv.shape[:2], dtype=np.uint8)

        # Объединяем диапазоны (например, два диапазона для красного) в одну маску
        for lower, upper in ranges:
            mask = cv2.bitwise_or(mask, cv2.inRange(hsv, lower, upper))

        # Находим контуры объектов текущего цвета
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Проходим по каждому найденному контуру
        for cnt in contours:
            # Фильтруем мелкий шум (подберите значение под ваш размер объектов)
            if cv2.contourArea(cnt) < 50:
                continue

            # Строим баундинг бокс
            x, y, w, h = cv2.boundingRect(cnt)

            

            # Вычисляем центр
            center_x = x + w // 2
            center_y = y + h // 2

            cv2.circle(img_orig, (center_x, center_y), 5, (40, 40, 40), -1)


            # Добавляем в результат: [цвет, (x, y)]
            result.append([color_name, (center_x, center_y)])

    cv2.imshow("colors", img_orig)
    cv2.waitKey(0)
    return result




def build_road_graph(all_pairs, colored_objects):
    # Словарь перевода цвета в цифру
    color_code = {"green": 1, "yellow": 2, "red": 3}
    
    # Готовим словарь для ответов {1: [], 2: [], 3: [], ...}
    result = {}
    for node1, node2 in all_pairs:
        result[node1[0]] = []
        result[node2[0]] = []

    # ТУПОЙ ПЕРЕБОР: берем каждую пару перекрестков
    for (id1, x1, y1), (id2, x2, y2) in all_pairs:
        found_colors = []

        # Перебираем ВСЕ найденные цветные кусочки
        for color_name, (cx, cy) in colored_objects:
            
            # 1. Проверяем, вписывается ли цветная точка в габариты между x1..x2 и y1..y2 (с запасом в 20px)
            if (min(x1, x2) - 20 <= cx <= max(x1, x2) + 20) and \
               (min(y1, y2) - 20 <= cy <= max(y1, y2) + 20):
                
                # 2. Тупо считаем сумму расстояний: (перекресток1 -> цвет) + (цвет -> перекресток2)
                d1 = np.hypot(cx - x1, cy - y1)
                d2 = np.hypot(cx - x2, cy - y2)
                d_total = np.hypot(x2 - x1, y2 - y1) # Длина прямой от П1 до П2
                
                # Если точка лежит НА прямой, то d1 + d2 лишь чуть-чуть больше, чем d_total
                # (допуск 15 пикселей на неровности)
                if abs((d1 + d2) - d_total) < 5:
                    found_colors.append((d1, color_code[color_name]))

        # Если на этой линии нашлись цветные кусочки — значит между ними ЕСТЬ дорога!
        if found_colors:
            # Сортируем кусочки по расстоянию от 1-го перекрестка (d1)
            found_colors.sort(key=lambda item: item[0])
            
            # Порядок цветов от П1 к П2
            road_from_1 = [c[1] for c in found_colors]
            # Порядок цветов от П2 к П1 (просто разворачиваем)
            road_from_2 = road_from_1[::-1]
            
            result[id1].append(road_from_1)
            result[id2].append(road_from_2)

    # Форматируем ключи в строки ("1", "2"...)
    return {str(k): v for k, v in sorted(result.items())}




if __name__ == "__main__":
    image_path = "/home/arrma/PROGRAMMS/Olimp_2026/TASKS/141/images/5173b78f-02c4-4ad3-aed7-c923e2771fae.jpg" 

    img = cv2.imread(image_path)

    # 1. Ищем черные перекрестки (поправь у себя gray = cv2.cvtColor(image, ...))
    centers = find_black_objects(img)
    sorted_centers = sort_tuples_by_first_element(centers)

    # 2. Генерируем все пары
    all_pairs = get_all_pairs(sorted_centers)

    # 3. Ищем цветные плашки
    colored_objects = find_colored_objects(img)

    # 4. Тупо связываем их в готовый граф
    ans = build_road_graph(all_pairs, colored_objects)
    
    print("\nИТОГОВЫЙ СЛОВАРЬ:")
    print(ans)