#!/usr/bin/env bash

python3 -c '
import os, re, urllib.parse

def convert_obsidian_syntax(text):
    # 1. Замена изображений: ![[path/img.png|Alt]] -> ![Alt](path/img.png)
    def img_repl(match):
        path = match.group(1).strip()
        alt = match.group(2) if match.group(2) else ""
        encoded_path = urllib.parse.quote(path, safe="/#?")
        return f"![{alt}]({encoded_path})"

    # 2. Замена текстовых вики-ссылок: [[path/note|Текст]] -> [Текст](path/note.md)
    def doc_repl(match):
        path = match.group(1).strip()
        label = match.group(2) if match.group(2) else path.split("/")[-1]
        
        if "." not in path.split("/")[-1]:
            path += ".md"
            
        encoded_path = urllib.parse.quote(path, safe="/#?")
        return f"[{label}]({encoded_path})"

    # Сначала обрабатываем изображения ![[...]], затем обычные ссылки [[...]]
    text = re.sub(r"!\[\[([^\|\]]+)(?:\|([^\]]+))?\]\]", img_repl, text)
    text = re.sub(r"(?<!\!)\[\[([^\|\]]+)(?:\|([^\]]+))?\]\]", doc_repl, text)
    return text

updated_files = 0
for root, _, files in os.walk("."):
    for file in files:
        if file.endswith(".md"):
            filepath = os.path.join(root, file)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                
                new_content = convert_obsidian_syntax(content)
                
                if new_content != content:
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    print(f"[+] Изменен: {filepath}")
                    updated_files += 1
            except Exception as e:
                print(f"[!] Ошибка при обработке {filepath}: {e}")

print(f"\nГотово. Обновлено файлов: {updated_files}")
'
