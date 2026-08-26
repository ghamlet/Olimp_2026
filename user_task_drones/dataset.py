import shutil

from pathlib import Path

  
  

# указываем путь до датасета YOLODataset, внутри которого будут папки images , labels

# рядом с этой папкой после выполнения скрипта появиться папка obj в которой будут одновременно фотографии и аннотации

  

PATH = "/home/arrma/Documents/Olimp_2026/user_task_drones/images/YOLODataset"

  
  
# здесь ничего не меняем -------------------------------------

SRC = Path(PATH)

OBJ = SRC / "obj"

OBJ.mkdir(exist_ok=True)

  

exts = {".jpg", ".jpeg", ".png", ".bmp"}

  

for src_dir, exts_group in [(SRC / "images", exts), (SRC / "labels", {".txt"})]:

    for f in src_dir.rglob("*"):

        if f.suffix.lower() in exts_group:

            shutil.copy2(f, OBJ / f.name)



print(f"Готово. Файлов в obj/: {len(list(OBJ.iterdir()))}")
