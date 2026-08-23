# -*- coding: utf-8 -*-
"""
Файл служит для определения точности вашего алгоритма

Для получения оценки точности, запустите файл на исполнение
"""
import json

import cv2

import eval as submission
# import solution as submission


def main():
    annot_file = "annotations.json"

    with open(annot_file, 'r') as f:
        annot_data = json.load(f)

    correct = 0
    for image_filename, cross_data in annot_data.items():
        image = cv2.imread('images/' + image_filename)

        user_answer = submission.analyze_traffic(image)

        for cross_roads in cross_data.values():
            cross_roads.sort()
        
        for cross_roads in user_answer.values():
            cross_roads.sort()

        if user_answer == cross_data:
            correct += 1

    total_object = len(annot_data)
    print(f"Из {total_object} предсказаний верны {correct}")

    score = correct / total_object
    print(f"Точность: {score:.2f}")


if __name__ == '__main__':
    main()