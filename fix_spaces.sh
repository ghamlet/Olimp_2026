#!/usr/bin/env bash

python3 -c '
import os, re, urllib.parse

def convert_clean_spaces(text):
    # 1. Вики-картинки -> ![](path/file name.png)
    def img_wiki_repl(match):
        path = match.group(1).strip()
        alt = match.group(2) if match.group(2) else ""
        path = urllib.parse.unquote(path).strip("<>")
        return f"![{alt}]({path})"

    # 2. Вики-заметки -> [Label](path/note name.md)
    def doc_wiki_repl(match):
        path = match.group(1).strip()
        label = match.group(2) if match.group(2) else path.split("/")[-1]
        path = urllib.parse.unquote(path).strip("<>")
        if "." not in path.split("/")[-1]:
            path += ".md"
        return f"[{label}]({path})"

    # 3. Чистка ссылок (убираем <> и %20)
    def md_clean(match):
        prefix = match.group(1)
        path = match.group(2).strip().strip("<>")
        path = urllib.parse.unquote(path)
        return f"{prefix}({path})"

    text = re.sub(r"!\[\[([^\|\]]+)(?:\|([^\]]+))?\]\]", img_wiki_repl, text)
    text = re.sub(r"(?<!\!)\[\[([^\|\]]+)(?:\|([^\]]+))?\]\]", doc_wiki_repl, text)
    text = re.sub(r"(!?\[.*?\])\((.*?)\)", md_clean, text)
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
                
                new_content = convert_clean_spaces(content)
                
                if new_content != content:
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    print(f"[+] {filepath}")
                    updated_files += 1
            except Exception as e:
                print(f"[!] Ошибка {filepath}: {e}")

print(f"\nГотово! Обновлено файлов: {updated_files}")
'
