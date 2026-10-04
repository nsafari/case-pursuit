"""
بازوی پیگیری کیس‌های حقوقی
Bale Messenger Bot for Legal Case Tracking
پشتیبانی از چندین پرونده
"""

import os
import sys
import time
import logging
import requests
from pathlib import Path
from case_manager import CaseManager
from config import BOT_TOKEN, CASES_DIR, LOG_LEVEL

# تنظیم لاگر
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LegalCaseBot:
    """بازوی پیگیری کیس‌های حقوقی"""
    
    def __init__(self, token: str, cases_dir: str):
        """
        مقداردهی اولیه بازو
        
        Args:
            token: توکن بازوی بله
            cases_dir: مسیر پوشه کیس‌ها
        """
        self.token = token
        self.base_url = f"https://tapi.bale.ai/bot{token}/"
        self.case_manager = CaseManager(cases_dir)
        logger.info(f"بازو راه‌اندازی شد - مسیر کیس‌ها: {cases_dir}")
        logger.info(f"تعداد پرونده‌های یافت شده: {len(self.case_manager.cases)}")
    
    def send_message(self, chat_id: int, text: str, parse_mode: str = None, reply_markup: dict = None) -> dict:
        """
        ارسال پیام به کاربر
        
        Args:
            chat_id: شناسه چت
            text: متن پیام
            parse_mode: قالب متن (HTML یا Markdown)
            reply_markup: کیبورد یا دکمه‌ها
            
        Returns:
            پاسخ سرور
        """
        url = f"{self.base_url}sendMessage"
        payload = {"chat_id": chat_id, "text": text}
        if parse_mode:
            payload["parse_mode"] = parse_mode
        if reply_markup:
            payload["reply_markup"] = reply_markup
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"خطا در ارسال پیام: {e}")
            return {"ok": False, "error": str(e)}
    
    def answer_callback_query(self, callback_query_id: str, text: str = None) -> dict:
        """
        پاسخ به کلیک روی دکمه
        
        Args:
            callback_query_id: شناسه کوئری
            text: متن پاسخ (اختیاری)
            
        Returns:
            پاسخ سرور
        """
        url = f"{self.base_url}answerCallbackQuery"
        payload = {"callback_query_id": callback_query_id}
        if text:
            payload["text"] = text
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"خطا در پاسخ به کلیک: {e}")
            return {"ok": False, "error": str(e)}
    
    def get_updates(self, offset: int = None) -> dict:
        """
        دریافت پیام‌های جدید
        
        Args:
            offset: شناسه آخرین پیام دریافت شده
            
        Returns:
            لیست پیام‌ها
        """
        url = f"{self.base_url}getUpdates"
        params = {"timeout": 30}
        if offset:
            params["offset"] = offset
        
        try:
            response = requests.get(url, params=params, timeout=35)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"خطا در دریافت پیام‌ها: {e}")
            return {"ok": False, "error": str(e)}
    
    def handle_start(self, chat_id: int) -> str:
        """پاسخ به دستور /start"""
        cases = self.case_manager.get_all_cases()
        cases_text = ""
        
        if cases:
            cases_list = "\n".join([f"• {c['name']}" for c in cases])
            cases_text = f"\n\n📁 پرونده‌های موجود:\n{cases_list}\n\n💡 برای انتخاب پرونده: /select [نام پرونده]"
        else:
            cases_text = "\n\n⚠️ هنوز پرونده‌ای ثبت نشده است."
        
        return f"""👋 سلام!
به بازوی پیگیری کیس‌های حقوقی خوش آمدید.{cases_text}

📋 دستورات موجود:
/cases - لیست تمام پرونده‌ها
/select [نام] - انتخاب پرونده
/status - آخرین وضعیت پرونده انتخاب شده
/case - جزئیات پرونده
/deadline - مهلت‌های مهم
/documents - مدارک مورد نیاز
/scenarios - سناریوهای کارشناسی
/contact - اطلاعات تماس شعبه
/help - راهنمای دستورات"""
    
    def handle_help(self, chat_id: int) -> str:
        """پاسخ به دستور /help"""
        return """📖 راهنمای دستورات:

/start - شروع کار با بازو
/cases - نمایش لیست تمام پرونده‌ها
/select [نام پرونده] - انتخاب پرونده فعال
/status - نمایش آخرین وضعیت پرونده انتخاب شده
/case - نمایش جزئیات کامل پرونده
/deadline - نمایش مهلت‌های مهم و نزدیک
/documents - لیست مدارک مورد نیاز و موجود
/scenarios - نمایش سناریوهای ارائه به کارشناس
/contact - اطلاعات تماس و آدرس شعبه
/search [عبارت] - جستجو در پرونده‌ها

💡 نکته: ابتدا با /select یک پرونده انتخاب کنید."""
    
    def handle_cases(self, chat_id: int) -> str:
        """پاسخ به دستور /cases"""
        try:
            cases = self.case_manager.get_all_cases()
            
            if not cases:
                return "📁 هنوز پرونده‌ای در سیستم ثبت نشده است.\n\nپرونده‌ها را در پوشه cases/ اضافه کنید."
            
            current_case = self.case_manager.get_current_case_name()
            
            cases_text = []
            for i, case in enumerate(cases, 1):
                status = "🟢" if case['name'] == current_case else "⚪"
                cases_text.append(f"{status} {i}. {case['name']}")
                cases_text.append(f"   📋 شماره: {case['case_number']}")
                cases_text.append(f"   📝 موضوع: {case['subject']}")
                cases_text.append("")
            
            # ایجاد دکمه‌های شیشه‌ای
            inline_keyboard = []
            for case in cases:
                inline_keyboard.append([
                    {
                        "text": f"📁 {case['name']}",
                        "callback_data": f"select_{case['name']}"
                    }
                ])
            
            reply_markup = {
                "inline_keyboard": inline_keyboard
            }
            
            message = f"""📁 لیست پرونده‌ها ({len(cases)} پرونده):

{chr(10).join(cases_text)}

🟢 = پرونده فعلی
⚪ = پرونده‌های دیگر

💡 روی دکمه زیر کلیک کنید تا پرونده را انتخاب کنید:"""
            
            # ارسال پیام با دکمه‌ها
            self.send_message(chat_id, message, reply_markup=reply_markup)
            return None  # پیام قبلاً ارسال شده
        except Exception as e:
            logger.error(f"خطا در دریافت لیست پرونده‌ها: {e}")
            return "⚠️ خطا در دریافت اطلاعات. لطفاً بعداً تلاش کنید."
    
    def handle_select(self, chat_id: int, case_name: str) -> str:
        """پاسخ به دستور /select"""
        try:
            if not case_name:
                return "❌ لطفاً نام پرونده را وارد کنید.\n\nمثال: /select 01-nam-kis"
            
            if self.case_manager.select_case(case_name):
                return f"""✅ پرونده انتخاب شد: {case_name}

اکنون می‌توانید از دستورات زیر استفاده کنید:
/status - آخرین وضعیت
/case - جزئیات پرونده
/deadline - مهلت‌ها
/documents - مدارک
/contact - اطلاعات تماس"""
            else:
                # نمایش پرونده‌های موجود
                cases = self.case_manager.get_all_cases()
                cases_list = "\n".join([f"• {c['name']}" for c in cases])
                
                return f"""❌ پرونده '{case_name}' یافت نشد.

📁 پرونده‌های موجود:
{cases_list}

💡 از نام دقیق پرونده استفاده کنید."""
        except Exception as e:
            logger.error(f"خطا در انتخاب پرونده: {e}")
            return "⚠️ خطا در انتخاب پرونده. لطفاً بعداً تلاش کنید."
    
    def handle_status(self, chat_id: int) -> str:
        """پاسخ به دستور /status"""
        try:
            if not self.case_manager.current_case:
                return "❌ ابتدا یک پرونده انتخاب کنید.\n\nدستور: /cases"
            
            status = self.case_manager.get_case_status()
            return f"""📋 آخرین وضعیت پرونده: {status['case_name']}

🔢 شماره پرونده: {status['case_number']}
📝 موضوع: {status['subject']}
📌 وضعیت فعلی: {status['current_status']}

💰 وضعیت پرداخت:
{status['payment_status']}

🔄 آخرین به‌روزرسانی: {status['last_update']}"""
        except Exception as e:
            logger.error(f"خطا در دریافت وضعیت: {e}")
            return "⚠️ خطا در دریافت اطلاعات. لطفاً بعداً تلاش کنید."
    
    def handle_case(self, chat_id: int) -> str:
        """پاسخ به دستور /case"""
        try:
            if not self.case_manager.current_case:
                return "❌ ابتدا یک پرونده انتخاب کنید.\n\nدستور: /cases"
            
            case_info = self.case_manager.get_case_details()
            return f"""📄 جزئیات پرونده: {case_info['case_name']}

🔢 شماره پرونده: {case_info['case_number']}
📋 عنوان: {case_info['title']}

👥 طرفین پرونده:
خواهان: {case_info['plaintiff']}
خوانده: {case_info['defendant']}

🏛️ مرجع صالح: {case_info['court']}
📅 تاریخ شروع: {case_info['start_date']}"""
        except Exception as e:
            logger.error(f"خطا در دریافت جزئیات: {e}")
            return "⚠️ خطا در دریافت اطلاعات. لطفاً بعداً تلاش کنید."
    
    def handle_deadline(self, chat_id: int) -> str:
        """پاسخ به دستور /deadline"""
        try:
            if not self.case_manager.current_case:
                return "❌ ابتدا یک پرونده انتخاب کنید.\n\nدستور: /cases"
            
            deadlines = self.case_manager.get_deadlines()
            return f"""⏰ مهلت‌های مهم پرونده: {self.case_manager.get_current_case_name()}

✅ مراحل تکمیل شده:
{deadlines['completed']}

⏳ مراحل آینده:
{deadlines['upcoming']}

💡 برای اطلاعات بیشتر با شعبه تماس بگیرید."""
        except Exception as e:
            logger.error(f"خطا در دریافت مهلت‌ها: {e}")
            return "⚠️ خطا در دریافت اطلاعات. لطفاً بعداً تلاش کنید."
    
    def handle_documents(self, chat_id: int) -> str:
        """پاسخ به دستور /documents"""
        try:
            if not self.case_manager.current_case:
                return "❌ ابتدا یک پرونده انتخاب کنید.\n\nدستور: /cases"
            
            docs = self.case_manager.get_documents()
            return f"""📑 مدارک پرونده: {self.case_manager.get_current_case_name()}

✅ مدارک تکمیل شده:
{docs['completed']}

⏳ مدارک در حال تهیه:
{docs['pending']}

💡 نکته: مدارک تکمیل شده در پوشه پروژه موجود است."""
        except Exception as e:
            logger.error(f"خطا در دریافت مدارک: {e}")
            return "⚠️ خطا در دریافت اطلاعات. لطفاً بعداً تلاش کنید."
    
    def handle_contact(self, chat_id: int) -> str:
        """پاسخ به دستور /contact"""
        try:
            if not self.case_manager.current_case:
                return "❌ ابتدا یک پرونده انتخاب کنید.\n\nدستور: /cases"
            
            contact = self.case_manager.get_contact_info()
            return f"""📞 اطلاعات تماس شعبه:

🏛️ نام شعبه: {contact['branch_name']}
📍 آدرس: {contact['address']}
📞 تلفن: {contact['phone']}
🕐 ساعت کاری: {contact['working_hours']}

🗺️ مسیریابی: نام شعبه را در نقشه جستجو کنید"""
        except Exception as e:
            logger.error(f"خطا در دریافت اطلاعات تماس: {e}")
            return "⚠️ خطا در دریافت اطلاعات. لطفاً بعداً تلاش کنید."
    
    def handle_scenarios(self, chat_id: int) -> str:
        """پاسخ به دستور /scenarios"""
        try:
            if not self.case_manager.current_case:
                return "❌ ابتدا یک پرونده انتخاب کنید.\n\nدستور: /cases"
            
            scenarios = self.case_manager.get_scenarios()
            return f"""📋 سناریوهای پرونده: {self.case_manager.get_current_case_name()}

📌 موضوع: {scenarios['title']}

{scenarios['scenarios']}

💡 نکته: این سناریوها برای ارائه به کارشناس رسمی دادگستری تهیه شده‌اند."""
        except Exception as e:
            logger.error(f"خطا در دریافت سناریوها: {e}")
            return "⚠️ خطا در دریافت اطلاعات. لطفاً بعداً تلاش کنید."
    
    def handle_search(self, chat_id: int, query: str) -> str:
        """پاسخ به دستور /search"""
        try:
            if not query:
                return "❌ لطفاً عبارت جستجو را وارد کنید.\n\nمثال: /search تأمین دلیل"
            
            results = self.case_manager.search_cases(query)
            
            if not results:
                return f"🔍 نتیجه‌ای برای '{query}' یافت نشد."
            
            results_text = []
            for result in results:
                results_text.append(f"📁 {result['name']}")
                results_text.append(f"   📋 شماره: {result['case_number']}")
                results_text.append(f"   📝 موضوع: {result['subject']}")
                results_text.append("")
            
            return f"""🔍 نتایج جستجو برای '{query}':

{chr(10).join(results_text)}

💡 برای انتخاب پرونده:
/select [نام پرونده]"""
        except Exception as e:
            logger.error(f"خطا در جستجو: {e}")
            return "⚠️ خطا در جستجو. لطفاً بعداً تلاش کنید."
    
    def handle_callback_query(self, callback_query: dict) -> None:
        """
        پردازش کلیک روی دکمه‌های شیشه‌ای
        
        Args:
            callback_query: اطلاعات کلیک
        """
        callback_query_id = callback_query["id"]
        data = callback_query["data"]
        chat_id = callback_query["message"]["chat"]["id"]
        
        if data.startswith("select_"):
            case_name = data[7:]  # حذف "select_" از ابتدا
            
            if self.case_manager.select_case(case_name):
                self.answer_callback_query(callback_query_id, f"✅ پرونده {case_name} انتخاب شد")
                
                # ارسال پیام تأیید
                status = self.case_manager.get_case_status()
                message = f"""✅ پرونده انتخاب شد: {case_name}

📋 آخرین وضعیت:
شماره پرونده: {status['case_number']}
موضوع: {status['subject']}

💡 اکنون می‌توانید از دستورات زیر استفاده کنید:
/status - آخرین وضعیت
/case - جزئیات پرونده
/deadline - مهلت‌ها
/documents - مدارک
/contact - اطلاعات تماس"""
                self.send_message(chat_id, message)
            else:
                self.answer_callback_query(callback_query_id, "❌ خطا در انتخاب پرونده")
    
    def handle_message(self, chat_id: int, text: str) -> str:
        """
        پردازش پیام دریافتی و ارسال پاسخ مناسب
        
        Args:
            chat_id: شناسه چت
            text: متن پیام
            
        Returns:
            متن پاسخ
        """
        text = text.strip()
        text_lower = text.lower()
        
        if text_lower in ['/start', 'start']:
            return self.handle_start(chat_id)
        elif text_lower in ['/help', 'help']:
            return self.handle_help(chat_id)
        elif text_lower in ['/cases', 'cases']:
            return self.handle_cases(chat_id)
        elif text_lower.startswith('/select ') or text_lower == '/select':
            case_name = text[8:].strip() if len(text) > 8 else ""
            return self.handle_select(chat_id, case_name)
        elif text_lower in ['/status', 'status']:
            return self.handle_status(chat_id)
        elif text_lower in ['/case', 'case']:
            return self.handle_case(chat_id)
        elif text_lower in ['/deadline', 'deadline']:
            return self.handle_deadline(chat_id)
        elif text_lower in ['/documents', 'documents']:
            return self.handle_documents(chat_id)
        elif text_lower in ['/scenarios', 'scenarios']:
            return self.handle_scenarios(chat_id)
        elif text_lower in ['/contact', 'contact']:
            return self.handle_contact(chat_id)
        elif text_lower.startswith('/search '):
            query = text[8:].strip()
            return self.handle_search(chat_id, query)
        else:
            return f"❓ دستور نامعتبر: {text}\n\nبرای مشاهده دستورات، /help را ارسال کنید."
    
    def start(self):
        """شروع اجرای بازو"""
        logger.info("بازو در حال اجراست...")
        offset = None
        
        while True:
            try:
                updates = self.get_updates(offset)
                
                if updates.get("ok") and "result" in updates:
                    for update in updates["result"]:
                        offset = update["update_id"] + 1
                        
                        # پردازش کلیک روی دکمه‌ها
                        if "callback_query" in update:
                            self.handle_callback_query(update["callback_query"])
                        
                        # پردازش پیام‌های متنی
                        elif "message" in update:
                            message = update["message"]
                            chat_id = message["chat"]["id"]
                            text = message.get("text", "")
                            
                            if text:
                                logger.info(f"پیام دریافتی از {chat_id}: {text}")
                                response = self.handle_message(chat_id, text)
                                if response:  # اگر پاسخی برگردانده شد
                                    self.send_message(chat_id, response)
                                logger.info(f"پاسخ ارسال شده به {chat_id}")
                
                time.sleep(1)
                
            except KeyboardInterrupt:
                logger.info("بازو متوقف شد.")
                break
            except Exception as e:
                logger.error(f"خطا در حلقه اصلی: {e}")
                time.sleep(5)


def main():
    """تابع اصلی"""
    # بررسی توکن
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ خطا: توکن بازو تنظیم نشده است.")
        print("لطفاً فایل config.py را ویرایش کنید و توکن را وارد کنید.")
        print("توکن را از @BotFather در بله دریافت کنید.")
        sys.exit(1)
    
    # بررسی مسیر کیس‌ها
    if not os.path.exists(CASES_DIR):
        print(f"❌ خطا: مسیر کیس‌ها یافت نشد: {CASES_DIR}")
        sys.exit(1)
    
    # ایجاد و شروع بازو
    bot = LegalCaseBot(BOT_TOKEN, CASES_DIR)
    bot.start()


if __name__ == "__main__":
    main()
