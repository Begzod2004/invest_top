import os
from dotenv import load_dotenv

load_dotenv()

# Bot token ni .env faylidan olish
BOT_TOKEN = os.getenv("BOT_TOKEN", "6080036337:AAFlFZFp4YL-RnSu2YoLWZRIAS6FKX6CGbc")
CHANNEL_ID = os.getenv("CHANNEL_ID", "-1001953539625")  # Kanal ID

if not all([BOT_TOKEN, CHANNEL_ID]):
    raise ValueError("BOT_TOKEN va CHANNEL_ID .env faylida ko'rsatilishi kerak")

# String tipidagi CHANNEL_ID ni int ga o'tkazamiz
try:
    CHANNEL_ID = int(CHANNEL_ID)
except (TypeError, ValueError):
    raise ValueError("CHANNEL_ID raqam bo'lishi kerak")
