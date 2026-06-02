import sys
import os
import json
import base64
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError, PhoneCodeExpiredError

API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
HASH_FILE = "phone_hash.json"

async def send_code(phone, resend=False):
    client = TelegramClient(StringSession(), API_ID, API_HASH)
    await client.connect()

    try:
        if resend and os.path.exists(HASH_FILE):
            with open(HASH_FILE, "r") as f:
                data = json.load(f)
            if data["phone"] == phone:
                await client.disconnect()
                client = TelegramClient(StringSession(data["session"]), API_ID, API_HASH)
                await client.connect()

                result = await client.resend_code_request(phone, data["hash"])
                print(f"📞 کد مجدداً به {phone} ارسال شد")
                print(f"📱 نوع: {result.type}")

                data["hash"] = result.phone_code_hash
                data["session"] = client.session.save()
                with open(HASH_FILE, "w") as f:
                    json.dump(data, f)

                await client.disconnect()
                return

        result = await client.send_code_request(phone)

        with open(HASH_FILE, "w") as f:
            json.dump({
                "phone": phone,
                "hash": result.phone_code_hash,
                "session": client.session.save()
            }, f)

        print(f"✅ کد به {phone} ارسال شد")
        print(f"📱 نوع: {result.type}")
        if hasattr(result, 'next_type') and result.next_type:
            print(f"🔄 بعدی: {result.next_type} - از 'resend' استفاده کنید")

    except Exception as e:
        print(f"❌ خطا: {e}")
        sys.exit(1)
    finally:
        await client.disconnect()

async def verify_code(phone, code, password=None):
    if not os.path.exists(HASH_FILE):
        print("❌ ورود معلقی وجود ندارد. ابتدا بدون کد اجرا کنید")
        sys.exit(1)

    with open(HASH_FILE, "r") as f:
        data = json.load(f)

    if data["phone"] != phone:
        print(f"❌ شماره تلفن مطابقت ندارد")
        sys.exit(1)

    client = TelegramClient(StringSession(data["session"]), API_ID, API_HASH)
    await client.connect()

    try:
        await client.sign_in(phone, code, phone_code_hash=data["hash"])
    except SessionPasswordNeededError:
        if not password:
            print("🔐 رمز دو مرحله‌ای نیاز است. دوباره با رمز اجرا کنید")
            await client.disconnect()
            sys.exit(1)
        await client.sign_in(password=password)
    except PhoneCodeExpiredError:
        print("❌ کد منقضی شده. بدون کد اجرا کنید تا کد جدید دریافت کنید")
        os.remove(HASH_FILE)
        await client.disconnect()
        sys.exit(1)

    try:
        session_string = client.session.save()
        with open("im.im", "w") as f:
            f.write(base64.b64encode(session_string.encode()).decode())

        print("✅ ورود موفقیت‌آمیز بود!")
        if os.path.exists(HASH_FILE):
            os.remove(HASH_FILE)

    except Exception as e:
        print(f"❌ خطا: {e}")
        sys.exit(1)
    finally:
        await client.disconnect()

if __name__ == "__main__":
    phone = sys.argv[1] if len(sys.argv) > 1 else ""
    code = sys.argv[2] if len(sys.argv) > 2 else ""
    extra = sys.argv[3] if len(sys.argv) > 3 else ""

    if not phone:
        print("❌ استفاده: python login.py <شماره> [کد] [رمز_دومرحله‌ای]")
        sys.exit(1)

    if code == "resend":
        asyncio.run(send_code(phone, resend=True))
    elif code:
        asyncio.run(verify_code(phone, code, extra if extra else None))
    else:
        asyncio.run(send_code(phone))
