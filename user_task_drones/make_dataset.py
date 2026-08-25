import csv
import os
import shutil

CSV_PATH = "annotations.csv"
OBJ_DIR = "obj"


def main():
    os.makedirs(OBJ_DIR, exist_ok=True)

    boxes = {}
    with open(CSV_PATH, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            img_path = row["image"].strip()
            line = f"0 {row['x']} {row['y']} {row['w']} {row['h']}"
            boxes.setdefault(img_path, []).append(line)

    n_images, n_boxes = 0, 0
    for img_path, lines in boxes.items():
        src = img_path if os.path.exists(img_path) else os.path.join("images", os.path.basename(img_path))
        if not os.path.exists(src):
            print(f"skip {img_path}: cannot find")
            continue

        name = os.path.splitext(os.path.basename(img_path))[0]
        with open(os.path.join(OBJ_DIR, name + ".txt"), "w") as out:
            out.write("\n".join(lines) + "\n")
        shutil.copy2(src, OBJ_DIR)

        n_images += 1
        n_boxes += len(lines)

    print(f"Done: {n_images} images, {n_boxes} boxes -> ./{OBJ_DIR}")


if __name__ == "__main__":
    main()
