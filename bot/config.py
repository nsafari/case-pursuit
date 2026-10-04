"""
فایل پیکربندی بازوی پیگیری کیس‌های حقوقی
"""

import os
from pathlib import Path

# مسیر ریشه پروژه
PROJECT_ROOT = Path(__file__).parent.parent

# توکن بازوی بله
# ⚠️ توکن را از @BotFather در بله دریافت کنید
# ⚠️ هرگز توکن را در مکان‌های عمومی قرار ندهید
BOT_TOKEN = os.getenv("BALE_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# مسیر پوشه کیس‌ها
CASES_DIR = str(PROJECT_ROOT / "cases")

# تنظیمات لاگر
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# تنظیمات بازو
BOT_NAME = "بازوی پیگیری کیس‌های حقوقی"
BOT_DESCRIPTION = "پیگیری آخرین وضعیت کیس‌های حقوقی از طریق پیام‌رسان بله"

# قالب پیام‌ها
MESSAGES = {
    "welcome": """👋 سلام!
به بازوی پیگیری کیس‌های حقوقی خوش آمدید.

📋 دستورات موجود:
/status - آخرین وضعیت پرونده
/case - جزئیات پرونده
/deadline - مهلت‌های مهم
/documents - مدارک مورد نیاز
/scenarios - سناریوهای کارشناسی
/contact - اطلاعات تماس شعبه
/help - راهنمای دستورات

💡 برای شروع، دستور /status را ارسال کنید.""",
    
    "help": """📖 راهنمای دستورات:

/start - شروع کار با بازو
/status - نمایش آخرین وضعیت پرونده
/case - نمایش جزئیات کامل پرونده
/deadline - نمایش مهلت‌های مهم و نزدیک
/documents - لیست مدارک مورد نیاز و موجود
/scenarios - نمایش سناریوهای ارائه به کارشناس
/contact - اطلاعات تماس و آدرس شعبه

💡 نکته: تمام اطلاعات از فایل‌های پروژه خوانده می‌شود و به صورت خودکار به‌روز می‌شود.""",
    
    "error": "⚠️ خطا در دریافت اطلاعات. لطفاً بعداً تلاش کنید.",
    
    "invalid_command": "❓ دستور نامعتبر.\n\nبرای مشاهده دستورات، /help را ارسال کنید."
}

# تنظیمات امنیتی
SECURITY = {
    "allowed_chat_ids": [],  # لیست شناسه‌های چت مجاز (خالی = همه مجاز)
    "rate_limit": 10,  # حداکثر تعداد پیام در دقیقه
}

# تنظیمات ذخیره‌سازی
STORAGE = {
    "backup_dir": str(PROJECT_ROOT / "bot" / "backups"),
    "log_dir": str(PROJECT_ROOT / "bot" / "logs"),
}
