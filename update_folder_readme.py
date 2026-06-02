import os
import re

def format_size(size_bytes):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} TB"

def update_folder_readme(folder_path):
    readme_path = os.path.join(folder_path, "README.md")
    if not os.path.exists(readme_path):
        return

    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract existing info
    match = re.search(r'## 📥 فایل‌ها\n\| 📄 نام فایل \| 📏 حجم \|\n\|[-]+\|[-]+\|\n', content)
    if not match:
        return

    # Build new files table
    files_info = ""
    total_size = 0
    for f in sorted(os.listdir(folder_path)):
        if f == "README.md":
            continue
        fpath = os.path.join(folder_path, f)
        if os.path.isfile(fpath):
            size = os.path.getsize(fpath)
            total_size += size
            files_info += f"| [{f}](./{f}) | {format_size(size)} |\n"

    # Update total size
    content = re.sub(r'\| 📦 حجم کل \| .+ \|', f'| 📦 حجم کل | {format_size(total_size)} |', content)

    # Update files table
    new_table = f"## 📥 فایل‌ها\n| 📄 نام فایل | 📏 حجم |\n|------------|--------|\n{files_info}"
    content = re.sub(r'## 📥 فایل‌ها\n\| 📄 نام فایل \| 📏 حجم \|\n\|[-]+\|[-]+\|\n.*', new_table, content, flags=re.DOTALL)

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"📝 بروزرسانی شد: {readme_path}")

if __name__ == "__main__":
    downloads_dir = "downloads"
    for folder in os.listdir(downloads_dir):
        folder_path = os.path.join(downloads_dir, folder)
        if os.path.isdir(folder_path):
            update_folder_readme(folder_path)
