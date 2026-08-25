import csv
import os
import sys

import cv2

CSV_PATH = "annotations.csv"


def yolo_to_pixel(xc, yc, w, h, img_w, img_h):
    x1 = int(round((xc - w / 2) * img_w))
    y1 = int(round((yc - h / 2) * img_h))
    x2 = int(round((xc + w / 2) * img_w))
    y2 = int(round((yc + h / 2) * img_h))
    return x1, y1, x2, y2


def main():
    show = len(sys.argv) < 2 or sys.argv[1] != "--no-show"

    boxes = {}
    with open(CSV_PATH, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            img_path = row["image"].strip()
            xc, yc, w, h = map(float, (row["x"], row["y"], row["w"], row["h"]))
            boxes.setdefault(img_path, []).append((xc, yc, w, h))

    for img_path, objects in boxes.items():
        src = img_path if os.path.exists(img_path) else os.path.join("images", os.path.basename(img_path))
        img = cv2.imread(src)
        if img is None:
            print(f"skip {img_path}: cannot read")
            continue
        img_h, img_w = img.shape[:2]

        for i, (xc, yc, w, h) in enumerate(objects):
            x1, y1, x2, y2 = yolo_to_pixel(xc, yc, w, h, img_w, img_h)
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.circle(img, (x1, y1), 4, (0, 0, 255), -1)
            cv2.circle(img, (x2, y2), 4, (255, 0, 0), -1)
            cv2.putText(img, f"{i + 1}: drone", (x1, max(y1 - 6, 12)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        name = os.path.basename(img_path)
        print(f"{img_path}: {len(objects)} obj")

        if show:
            cv2.imshow("annotation", img)
            if cv2.waitKey(0) & 0xFF == ord("q"):
                show = False
                cv2.destroyAllWindows()

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
