"""
مدیریت پرونده‌های حقوقی
خواندن و پردازش اطلاعات از فایل‌های پروژه
پشتیبانی از چندین پرونده
"""

import os
from pathlib import Path
from typing import Dict, List, Optional


class CaseManager:
    """مدیریت پرونده‌های حقوقی"""
    
    def __init__(self, cases_dir: str):
        """
        مقداردهی اولیه
        
        Args:
            cases_dir: مسیر پوشه کیس‌ها
        """
        self.cases_dir = Path(cases_dir)
        if not self.cases_dir.exists():
            raise FileNotFoundError(f"پوشه کیس‌ها یافت نشد: {cases_dir}")
        
        # پرونده انتخاب شده فعلی
        self.current_case: Optional[Path] = None
        
        # پیدا کردن تمام پرونده‌ها
        self.cases = self._find_all_cases()
    
    def _find_all_cases(self) -> Dict[str, Path]:
        """
        پیدا کردن تمام پرونده‌های موجود
        
        Returns:
            دیکشنری حاوی نام و مسیر پرونده‌ها
        """
        cases = {}
        for item in self.cases_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                # بررسی وجود فایل‌های مورد نیاز
                if (item / "00-overview.md").exists():
                    cases[item.name] = item
        return cases
    
    def get_all_cases(self) -> List[Dict[str, str]]:
        """
        دریافت لیست تمام پرونده‌ها
        
        Returns:
            لیست پرونده‌ها با اطلاعات خلاصه
        """
        cases_list = []
        for name, path in self.cases.items():
            overview_file = path / "00-overview.md"
            if overview_file.exists():
                content = overview_file.read_text(encoding='utf-8')
                cases_list.append({
                    "name": name,
                    "case_number": self._extract_from_table(content, "شماره پرونده"),
                    "subject": self._extract_from_table(content, "عنوان کیس"),
                    "title": self._extract_from_table(content, "عنوان کیس")
                })
        return cases_list
    
    def select_case(self, case_name: str) -> bool:
        """
        انتخاب یک پرونده
        
        Args:
            case_name: نام پرونده
            
        Returns:
            آیا پرونده با موفقیت انتخاب شد؟
        """
        if case_name in self.cases:
            self.current_case = self.cases[case_name]
            return True
        return False
    
    def get_current_case_name(self) -> Optional[str]:
        """دریافت نام پرونده فعلی"""
        if self.current_case:
            return self.current_case.name
        return None
    
    def _read_file(self, filename: str) -> str:
        """
        خواندن محتوای فایل از پرونده فعلی
        
        Args:
            filename: نام فایل
            
        Returns:
            محتوای فایل
        """
        if not self.current_case:
            return ""
        
        filepath = self.current_case / filename
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        return ""
    
    def _extract_from_table(self, content: str, header: str) -> str:
        """
        استخراج مقدار از جدول مارک‌داون
        
        Args:
            content: محتوای فایل
            header: عنوان ستون
            
        Returns:
            مقدار استخراج شده
        """
        lines = content.split('\n')
        for line in lines:
            if header in line and '|' in line:
                parts = [p.strip() for p in line.split('|') if p.strip()]
                if len(parts) >= 3:
                    return parts[2]
        return ""
    
    def _extract_section(self, content: str, section_title: str) -> str:
        """
        استخراج یک بخش از محتوا
        
        Args:
            content: محتوای فایل
            section_title: عنوان بخش
            
        Returns:
            محتوای بخش
        """
        lines = content.split('\n')
        in_section = False
        section_content = []
        
        for line in lines:
            if section_title in line and ('##' in line or '###' in line):
                in_section = True
                continue
            elif in_section and line.startswith('#'):
                break
            elif in_section:
                section_content.append(line)
        
        return '\n'.join(section_content).strip()
    
    def _extract_list_items(self, content: str, marker: str) -> List[str]:
        """
        استخراج آیتم‌های یک لیست
        
        Args:
            content: محتوای فایل
            marker: نشانگر (مثلاً - [x] یا - [ ])
            
        Returns:
            لیست آیتم‌ها
        """
        items = []
        for line in content.split('\n'):
            if marker in line:
                item = line.replace(marker, '').strip()
                if item:
                    items.append(item)
        return items

    def _extract_bold_field(self, content: str, field: str) -> str:
        """
        استخراج مقدار یک فیلد متنی بولد (مثلاً **موضوع:** مقدار)

        از الگوی **فیلد:** مقدار یا فیلد:** مقدار پشتیبانی می‌کند

        Args:
            content: محتوای فایل
            field: نام فیلد مورد جستجو

        Returns:
            مقدار استخراج شده
        """
        marker = f'{field}:**'
        for line in content.split('\n'):
            stripped = line.strip()
            idx = stripped.find(marker)
            if idx != -1:
                return stripped[idx + len(marker):].strip()
        return ""

    def _extract_person_name(self, content: str, role: str) -> str:
        """
        استخراج نام شخص از بخش مربوطه (خواهان/خوانده)

        بخشی مثل ### خواهان را پیدا کرده و مقدار الگوی - **نام:** {value}
        را استخراج می‌کند

        Args:
            content: محتوای فایل
            role: نقش شخص (مثلاً خواهان یا خوانده)

        Returns:
            نام استخراج شده
        """
        name_marker = '- **نام:**'
        in_section = False
        for line in content.split('\n'):
            stripped = line.strip()
            if stripped.startswith('#') and role in stripped:
                in_section = True
                continue
            if in_section and stripped.startswith('#'):
                break
            if in_section and stripped.startswith(name_marker):
                return stripped[len(name_marker):].strip()
        return ""

    def _extract_from_timeline_table(self, content: str, section_title: str) -> List[str]:
        """
        استخراج رویدادها از جدول زمان‌بندی در یک بخش

        جدول‌هایی که سرستون آن‌ها «رویداد» داشته باشد (فرمت جدول زمان‌بندی)
        شناسایی شده و سطرها به صورت فرمت‌شده برگردانده می‌شوند

        Args:
            content: محتوای فایل
            section_title: عنوان بخش (مثلاً تاریخ‌های مهم گذشته)

        Returns:
            لیست رویدادها به صورت فرمت‌شده
        """
        in_section = False
        in_timeline_table = False
        events = []

        for line in content.split('\n'):
            stripped = line.strip()

            if not in_section:
                if stripped.startswith('#') and section_title in stripped:
                    in_section = True
                continue

            # پایان بخش: عنوان سطح # یا ## (زیربخش‌های ### ادامه دارند)
            if stripped.startswith('#') and not stripped.startswith('###'):
                break

            if not stripped.startswith('|'):
                in_timeline_table = False
                continue

            cells = [c.strip().replace('**', '') for c in stripped.split('|')]
            cells = [c for c in cells if c]
            if not cells:
                continue

            # ردیف جداکننده جدول (مثل |:---:|:---|)
            if all(set(c) <= set(':-') for c in cells):
                continue

            # تشخیص سرستون جدول زمان‌بندی
            if 'رویداد' in cells:
                in_timeline_table = True
                continue

            if in_timeline_table and len(cells) >= 2:
                date = cells[0]
                event = cells[1]
                description = cells[2] if len(cells) > 2 else ""
                if description:
                    events.append(f"{date} - {event} ({description})")
                else:
                    events.append(f"{date} - {event}")

        return events

    def get_case_status(self) -> Dict[str, str]:
        """
        دریافت وضعیت پرونده فعلی
        
        Returns:
            دیکشنری حاوی اطلاعات وضعیت
        """
        content = self._read_file("00-overview.md")

        # استخراج اطلاعات پرداخت از فایل
        payment_info = self._extract_section(content, "وضعیت پرونده")

        # وضعیت فعلی از زیربخش مرحله کنونی (فرمت استاندارد فایل‌ها)
        current_status = self._extract_section(content, "مرحله کنونی")
        if current_status:
            current_status = current_status.replace('**', '').strip()
        else:
            current_status = self._extract_section(content, "وضعیت فعلی")

        # آخرین به‌روزرسانی: اول از جدول، سپس از متن متنی (**آخرین به‌روزرسانی:** مقدار)
        last_update = self._extract_from_table(content, "آخرین به‌روزرسانی")
        if not last_update:
            last_update = self._extract_bold_field(content, "آخرین به‌روزرسانی")

        return {
            "case_name": self.get_current_case_name() or "نامشخص",
            "case_number": self._extract_from_table(content, "شماره پرونده"),
            "subject": self._extract_from_table(content, "عنوان کیس"),
            "current_status": current_status,
            "payment_status": payment_info if payment_info else "در انتظار بررسی",
            "last_update": last_update
        }
    
    def get_case_details(self) -> Dict[str, str]:
        """
        دریافت جزئیات پرونده فعلی
        
        Returns:
            دیکشنری حاوی جزئیات پرونده
        """
        content = self._read_file("00-overview.md")

        # نام طرفین از بخش‌های ### خواهان و ### خوانده (فرمت استاندارد فایل‌ها)
        plaintiff = self._extract_person_name(content, "خواهان")
        if not plaintiff and "خواهان" in content:
            plaintiff = self._extract_from_table(content, "نام")

        defendant = self._extract_person_name(content, "خوانده")
        if not defendant and "خوانده" in content:
            defendant = self._extract_from_table(content, "نام")

        return {
            "case_name": self.get_current_case_name() or "نامشخص",
            "case_number": self._extract_from_table(content, "شماره پرونده"),
            "title": self._extract_from_table(content, "عنوان کیس"),
            "plaintiff": plaintiff,
            "defendant": defendant,
            "court": self._extract_from_table(content, "مرجع صالح"),
            "start_date": self._extract_from_table(content, "تاریخ شروع")
        }
    
    def get_deadlines(self) -> Dict[str, str]:
        """
        دریافت مهلت‌های پرونده فعلی
        
        Returns:
            دیکشنری حاوی مهلت‌ها
        """
        content = self._read_file("01-timeline.md")

        # تلاش اول: فرمت چک‌لیست (- [x] / - [ ])
        completed = self._extract_section(content, "تاریخ‌های مهم گذشته")
        completed_items = self._extract_list_items(completed, "- [x]") if completed else []

        upcoming = self._extract_section(content, "تاریخ‌های مهم آینده")
        upcoming_items = self._extract_list_items(upcoming, "- [ ]") if upcoming else []

        # تلاش دوم: فرمت جدول زمان‌بندی
        if not completed_items:
            completed_items = self._extract_from_timeline_table(content, "تاریخ‌های مهم گذشته")

        if not upcoming_items:
            upcoming_items = self._extract_from_timeline_table(content, "تاریخ‌های مهم آینده")

        return {
            "completed": '\n'.join([f"✅ {item}" for item in completed_items]) if completed_items else "ندارد",
            "upcoming": '\n'.join([f"⏳ {item}" for item in upcoming_items]) if upcoming_items else "در انتظار"
        }
    
    def get_documents(self) -> Dict[str, str]:
        """
        دریافت لیست مدارک پرونده فعلی
        
        Returns:
            دیکشنری حاوی لیست مدارک
        """
        content = self._read_file("04-documents.md")
        
        completed_items = self._extract_list_items(content, "- [x]")
        pending_items = self._extract_list_items(content, "- [ ]")
        
        return {
            "completed": '\n'.join([f"✅ {item}" for item in completed_items]) if completed_items else "ندارد",
            "pending": '\n'.join([f"⏳ {item}" for item in pending_items]) if pending_items else "ندارد"
        }
    
    def get_contact_info(self) -> Dict[str, str]:
        """
        دریافت اطلاعات تماس پرونده فعلی
        
        Returns:
            دیکشنری حاوی اطلاعات تماس
        """
        # خواندن اطلاعات تماس از فایل مکاتبات (فرمت استاندارد)
        contact_content = self._read_file("06-correspondence.md")
        contact_section = self._extract_section(contact_content, "اطلاعات تماس شعبه") if contact_content else ""

        branch_name = ""
        address = ""
        phone = ""
        working_hours = ""

        if contact_section:
            branch_name = self._extract_from_table(contact_section, "نام شعبه")
            address = self._extract_from_table(contact_section, "آدرس")
            phone = self._extract_from_table(contact_section, "تلفن")
            working_hours = self._extract_from_table(contact_section, "ساعت کاری")

        # نام شعبه: اول از فایل مکاتبات، سپس از مرجع صالح در خلاصه پرونده
        if not branch_name:
            overview = self._read_file("00-overview.md")
            branch_name = self._extract_from_table(overview, "مرجع صالح")

        # پیش‌فرض‌ها فقط در صورت نبود فایل یا بخش
        return {
            "branch_name": branch_name or "[نام شعبه]",
            "address": address or "[آدرس شعبه]",
            "phone": phone or "[تلفن شعبه]",
            "working_hours": working_hours or "[ساعت کاری شعبه]"
        }
    
    def get_scenarios(self) -> Dict[str, str]:
        """
        دریافت سناریوهای پرونده فعلی
        
        Returns:
            دیکشنری حاوی سناریوها
        """
        content = self._read_file("07-expert-scenarios.md")
        if not content:
            content = self._read_file("03-opponent-moves.md")
        
        if not content:
            return {
                "title": "سناریوها",
                "scenarios": "ندارد",
                "summary": "فایل سناریوها برای این پرونده یافت نشد."
            }
        
        # عنوان: اول از جدول، سپس از الگوی بولد (**موضوع:** مقدار)
        title = self._extract_from_table(content, "موضوع")
        if not title:
            title = self._extract_bold_field(content, "موضوع")
        if not title:
            title = "سناریوها"
        scenarios_text = self._extract_scenarios_from_content(content)
        summary = self._extract_section(content, "پیشنهادات کلی") or self._extract_section(content, "خلاصه تحلیل") or ""
        
        return {
            "title": title,
            "scenarios": scenarios_text if scenarios_text else "ندارد",
            "summary": summary
        }
    
    def _extract_scenarios_from_content(self, content: str) -> str:
        """
        استخراج سناریوها از محتوای فایل مارک‌داون
        
        Args:
            content: محتوای فایل
            
        Returns:
            متن فرمت‌شده سناریوها
        """
        lines = content.split('\n')
        scenarios = []
        current_scenario = None
        in_scenario = False
        
        for line in lines:
            if line.startswith('## سناریوی'):
                if current_scenario:
                    scenarios.append(current_scenario)
                current_scenario = {
                    "title": line.replace('## ', '').strip(),
                    "content": []
                }
                in_scenario = True
            elif in_scenario and line.startswith('## ') and not line.startswith('###'):
                if current_scenario:
                    scenarios.append(current_scenario)
                current_scenario = None
                in_scenario = False
            elif in_scenario and current_scenario and line.strip():
                current_scenario["content"].append(line.strip())
        
        if current_scenario:
            scenarios.append(current_scenario)
        
        if not scenarios:
            return ""
        
        result = []
        for scenario in scenarios:
            result.append(f"**{scenario['title']}**")
            content_text = '\n'.join(scenario['content'])
            
            intro_match = self._extract_section_from_text(content_text, "نحوه معرفی")
            if intro_match:
                result.append(f"📝 نحوه معرفی:")
                result.append(intro_match)
            
            docs_match = self._extract_section_from_text(content_text, "مستندات")
            if docs_match:
                result.append(f"📎 مستندات مورد نیاز:")
                result.append(docs_match)
            
            note_match = self._extract_section_from_text(content_text, "نکته مهم")
            if note_match:
                result.append(f"⚠️ نکته مهم:")
                result.append(note_match)
            
            explain_match = self._extract_section_from_text(content_text, "توضیح")
            if explain_match:
                result.append(f"📝 توضیح:")
                result.append(explain_match)
            
            response_match = self._extract_section_from_text(content_text, "پاسخ ما")
            if response_match:
                result.append(f"🛡️ پاسخ ما:")
                result.append(response_match)
            
            probability_match = self._extract_section_from_text(content_text, "احتمال وقوع")
            if probability_match:
                result.append(f"📊 احتمال وقوع: {probability_match}")
            
            result.append("")
        
        return '\n'.join(result)
    
    def _extract_section_from_text(self, content: str, section_title: str) -> str:
        """
        استخراج بخش از متن بر اساس عنوان
        
        Args:
            content: متن ورودی
            section_title: عنوان بخش مورد جستجو
            
        Returns:
            محتوای بخش استخراج شده
        """
        lines = content.split('\n')
        in_section = False
        section_content = []
        
        for line in lines:
            if section_title in line and ('###' in line or '**' in line):
                inline_value = line.split(':', 1)[1].strip() if ':' in line else ''
                if inline_value:
                    return inline_value.replace('**', '').strip()
                in_section = True
                continue
            elif in_section and (line.startswith('###') or line.startswith('##')):
                break
            elif in_section and line.strip():
                section_content.append(line.strip())
        
        return '\n'.join(section_content).strip()
    
    def search_cases(self, query: str) -> List[Dict[str, str]]:
        """
        جستجو در پرونده‌ها
        
        Args:
            query: عبارت جستجو
            
        Returns:
            لیست پرونده‌های مطابق
        """
        results = []
        query_lower = query.lower()
        
        for name, path in self.cases.items():
            overview_file = path / "00-overview.md"
            if overview_file.exists():
                content = overview_file.read_text(encoding='utf-8')
                if query_lower in content.lower() or query_lower in name.lower():
                    results.append({
                        "name": name,
                        "case_number": self._extract_from_table(content, "شماره پرونده"),
                        "subject": self._extract_from_table(content, "عنوان کیس")
                    })
        
        return results
