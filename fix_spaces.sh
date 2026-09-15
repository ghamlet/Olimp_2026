#!/usr/bin/env bash

python3 -c '
import os, re, urllib.parse

def remove_exclamation(text):
    # 1. Вики-вставки ![[path/file.png|Alt]] -> [Alt](path/file.png)
    def img_wiki_repl(match):
        path = match.group(1).strip()
        label = match.group(2) if match.group(2) else path.split("/")[-1]
        path = urllib.parse.unquote(path).strip("<>")
        return f"[{label}]({path})"

    # 2. Обычные Markdown-картинки ![alt](path) -> [alt](path)
    def md_img_repl(match):
        alt = match.group(1)
        path = match.group(2).strip().strip("<>")
        path = urllib.parse.unquote(path)
        return f"[{alt}]({path})"

    text = re.sub(r"!\[\[([^\|\]]+)(?:\|([^\]]+))?\]\]", img_wiki_repl, text)
    text = re.sub(r"!\[(.*?)\]\((.*?)\)", md_img_repl, text)
    return text

updated_files = 0
for root, _, files in os.walk("."):
    if ".git" in root or ".obsidian" in root:
        continue
    for file in files:
        if file.endswith(".md"):
            filepath = os.path.join(root, file)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                
                new_content = remove_exclamation(content)
                
                if new_content != content:
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    print(f"[+] {filepath}")
                    updated_files += 1
            except Exception as e:
                print(f"[!] Ошибка {filepath}: {e}")

print(f"\nГотово! Восклицательные знаки выпилены. Обновлено файлов: {updated_files}")
'
