import os
import re
import sys
import base64
import asyncio
from datetime import datetime
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import MessageMediaDocument, MessageMediaPhoto, PeerChannel
API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
def get_session():
    if not os.path.exists("im.im"):
        print("❌ سشن یافت نشد. ابتدا ورکفلو Login را اجرا کنید.")
        sys.exit(1)
    with open("im.im", "r") as f:
        data = base64.b64decode(f.read()).decode()
    return data
def format_size(size_bytes):
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} TB"
def create_folder_readme(folder_path, persian_title, telegram_url, channel, msg_id):
    readme_path = f"{folder_path}/README.md"
    date_str = datetime.now().strftime("%Y/%m/%d - %H:%M")
    files_info = ""
    total_size = 0
    for f in os.listdir(folder_path):
        if f == "README.md":
            continue
        fpath = os.path.join(folder_path, f)
        if os.path.isfile(fpath):
            size = os.path.getsize(fpath)
            total_size += size
            files_info += f"| [{f}](./{f}) | {format_size(size)} |\n"
    content = f"""# 📁 {persian_title}
## 📋 اطلاعات

| 🏷️ | 📝 |
| :--- | :--- |
| 📅 تاریخ دانلود | {date_str} |
| 📢 کانال/گروه | {channel} |
| 🔢 شناسه پیام | {msg_id} |
| 🔗 لینک تلگرام | [باز کردن]({telegram_url}) |
| 📦 حجم کل | {format_size(total_size)} |

## 📥 فایل‌ها

| 📄 نام فایل | 📏 حجم |
| :--- | :--- |

{files_info}
"""
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(content)
def update_readme(folder_name, persian_title, telegram_url):
    readme_path = "downloads/README.md"
    date_str = datetime.now().strftime("%Y/%m/%d - %H:%M")
    new_entry = (
        f"| [{persian_title}](./{folder_name}) | "
        f"[لینک تلگرام]({telegram_url}) | {date_str} |\n"
    )
    if os.path.exists(readme_path):
        with open(readme_path, "a", encoding="utf-8") as f:
            f.write(new_entry)
    else:
        header = """# 📥 دانلودها

| 📁 پوشه | 🔗 لینک | 📅 تاریخ |
| :--- | :--- | :--- |

"""
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(header + new_entry)
async def resolve_message(client, telegram_url):
    """
    پارس هوشمند لینک‌های تلگرام بر اساس موقعیت مقادیر در آدرس
    """
    telegram_url = telegram_url.strip()
    
    # حذف پارامترهای اضافی انتهای لینک
    clean_url = telegram_url.split('?')[0]
    parts = clean_url.rstrip('/').split('/')
    
    try:
        if "t.me/c/" in clean_url:
            # پیدا کردن موقعیت بخش 'c' در لینک
            c_index = parts.index('c')
            
            # آیدی کانال دقیقاً اولین بخش بعد از 'c' است
            group_id = parts[c_index + 1]
            # آیدی پیام همیشه آخرین بخش لینک است
            msg_id = int(parts[-1])
            
            # پاکسازی و استخراج آیدی عددی خالص
            raw_id = int(str(group_id).replace("-100", ""))
            
            # معرفی صریح به عنوان کانال جهت جلوگیری از ChatIdInvalidError
            peer = PeerChannel(raw_id)
            
            entity = await client.get_entity(peer)
            message = await client.get_messages(entity, ids=msg_id)
            return entity, message, f"-100{raw_id}", msg_id
            
        else:
            # لینک عمومی (مانند t.me/username/1234)
            channel = parts[-2]
            msg_id = int(parts[-1])
            
            entity = await client.get_entity(channel)
            message = await client.get_messages(entity, ids=msg_id)
            return entity, message, channel, msg_id
            
    except Exception as e:
        print(f"❌ خطای پارس کردن لینک یا دریافت پیام از تلگرام: {e}")
        raise ValueError("Unsupported or invalid Telegram URL")
async def download_file(telegram_url, persian_title=None):
    session = get_session()
    client = TelegramClient(
        StringSession(session),
        API_ID,
        API_HASH
    )
    await client.connect()
    if not await client.is_user_authorized():
        print("❌ سشن منقضی شده")
        return None
    try:
        entity, message, channel_name, msg_id = await resolve_message(
            client,
            telegram_url
        )
        if not message:
            print("❌ پیام پیدا نشد")
            return None
        folder_name = persian_title or f"msg_{msg_id}"
        folder_name = re.sub(r'[<>:"/\\|?*]', "_", folder_name)
        folder_path = f"downloads/{folder_name}"
        os.makedirs(folder_path, exist_ok=True)
        downloaded = []
        if getattr(message, "grouped_id", None):
            msgs = await client.get_messages(entity, limit=100)
            messages = [
                m for m in msgs
                if getattr(m, "grouped_id", None) == message.grouped_id
            ]
            messages.sort(key=lambda x: x.id)
        else:
            messages = [message]
        for m in messages:
            if not m.media:
                continue
            if isinstance(m.media, MessageMediaDocument):
                fname = None
                for attr in m.media.document.attributes:
                    if hasattr(attr, "file_name"):
                        fname = attr.file_name
                        break
                if not fname:
                    mime = m.media.document.mime_type or "application/bin"
                    ext = mime.split("/")[-1]
                    fname = f"file_{m.id}.{ext}"
            elif isinstance(m.media, MessageMediaPhoto):
                fname = f"photo_{m.id}.jpg"
            else:
                fname = f"media_{m.id}"
            path = os.path.join(folder_path, fname)
            print(f"📥 دانلود {fname}")
            await client.download_media(m, path)
            downloaded.append(path)
        if not downloaded:
            print("❌ فایل قابل دانلودی پیدا نشد")
            return None
        create_folder_readme(
            folder_path,
            persian_title or folder_name,
            telegram_url,
            channel_name,
            msg_id
        )
        update_readme(
            folder_name,
            persian_title or folder_name,
            telegram_url
        )
        return downloaded
    finally:
        await client.disconnect()
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python download.py <telegram_url> [title]")
        sys.exit(1)
    url = sys.argv[1]
    title = sys.argv[2] if len(sys.argv) > 2 else None
    asyncio.run(download_file(url, title))
