# -*- coding: utf-8 -*-
"""
Файл служит для определения точности вашего алгоритма

Для получения оценки точности, запустите файл на исполнение
"""

import cv2
import pandas as pd

import eval as submission
# import solution as submission


def IoU(rect1, rect2):
    xc1, yc1, w1, h1 = rect1
    xc2, yc2, w2, h2 = rect2

    x1 = xc1 - w1 / 2
    y1 = yc1 - h1 / 2
    x2 = xc2 - w2 / 2
    y2 = yc2 - h2 / 2

    x_left = max(x1, x2)
    y_top = max(y1, y2)
    x_right = min(x1 + w1, x2 + w2)
    y_bottom = min(y1 + h1, y2 + h2)

    if x_right < x_left or y_bottom < y_top:
        return 0.0

    intersection_area = (x_right - x_left) * (y_bottom - y_top)
    rect1_area = w1 * h1
    rect2_area = w2 * h2
    union_area = rect1_area + rect2_area - intersection_area
    return intersection_area / union_area


def main():
    csv_file = "annotations.csv"
    data = pd.read_csv(csv_file, sep=',')
    data = data.sample(frac=1)

    models = submission.load_models()

    correct = 0
    for row in data.itertuples():
        _, image_filename, xc_r, yc_r, w_r, h_r = row
        xc_r, yc_r, w_r, h_r = map(float, [xc_r, yc_r, w_r, h_r])

        image = cv2.imread(image_filename)
        img_h, img_w = image.shape[:2]

        answer = (img_w * xc_r, img_h * yc_r, img_w * w_r, img_h * h_r)

        user_answer = submission.detect_drone(image, models)
        print(user_answer)
        if IoU(user_answer, answer) > 0.7:
            correct += 1

    total_object = len(data.index)
    print(f"Из {total_object} предсказаний верны {correct}")

    score = correct / total_object
    print(f"Точность: {score:.2f}")


if __name__ == '__main__':
    main()