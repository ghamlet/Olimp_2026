# -*- coding: utf-8 -*-
"""
Файл служит для определения точности вашего алгоритма

Для получения оценки точности, запустите файл на исполнение
"""

import eval as submission
import cv2
import pandas as pd
import numpy as np


def main():
    csv_file = "annotations.csv"
    data = pd.read_csv(csv_file, sep=';')  # TODO: check for , or ;
    data = data.sample(frac=1)

    tools = submission.load_tools()
    correct = 0
    for i, row in enumerate(data.itertuples()):
        row_id, video_file, matrix = row
        real_answer = np.array(eval(matrix), dtype=np.uint8)

        video = cv2.VideoCapture(video_file)

        user_answer = submission.track_movement(video, tools)

        if np.array_equal(user_answer, real_answer):
            correct += 1

    total_object = len(data.index)
    print(f"Из {total_object} объектов верно определены {correct}.")

    score = correct / total_object
    print(f"Точность: {score:.2f}")


if __name__ == '__main__':
    main()