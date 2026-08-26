
import cv2
import pandas as pd


def yolo_to_pixel(xc, yc, w, h, img_w, img_h):
    """Конвертация YOLO-формата (нормализованные координаты) в пиксели.
    YOLO: (xc, yc) - центр бокса, (w, h) - ширина/высота, все в диапазоне [0, 1].
    Возвращает: (x1, y1, x2, y2) - углы бокса в пикселях."""
    x1 = int(round((xc - w / 2) * img_w))
    y1 = int(round((yc - h / 2) * img_h))
    x2 = int(round((xc + w / 2) * img_w))
    y2 = int(round((yc + h / 2) * img_h))
    return x1, y1, x2, y2


def main():

    csv_file = "annotations.csv"
    data = pd.read_csv(csv_file, sep=',')
    # Перемешиваем данные для случайного порядка отображения
    data = data.sample(frac=1)

    # Формат CSV: image, x, y, w, h (координаты в YOLO-формате)
    for row in data.itertuples():
        _, img_path, xc, yc, w, h = row
        xc, yc, w, h = map(float, [xc, yc, w, h])

        img = cv2.imread(img_path)
        if img is None:
            print(f"skip {img_path}: cannot read")
            continue


        img_h, img_w = img.shape[:2]  # п

        # Рисуем bounding box и метки
        x1, y1, x2, y2 = yolo_to_pixel(xc, yc, w, h, img_w, img_h)
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)  # зеленый прямоугольник
        cv2.circle(img, (x1, y1), 4, (0, 0, 255), -1)  # красная точка - верхний левый угол
        cv2.circle(img, (x2, y2), 4, (255, 0, 0), -1)  # синяя точка - нижний правый угол
        cv2.putText(img, "drone", (x1, max(y1 - 6, 12)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        print(f"{img_path}: 1 obj")

        # Показываем изображение и ждем нажатия клавиши (q - выход)
    
        cv2.imshow("annotation", img)
        if cv2.waitKey(0) & 0xFF == ord("q"):
            cv2.destroyAllWindows()



if __name__ == "__main__":
    main()
