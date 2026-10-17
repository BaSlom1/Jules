import sys
import threading
import webbrowser
import urllib.parse
import ctypes
import locale
import re
try:
    import customtkinter as ctk
except ImportError:
    import tkinter as ctk

from registry_manager import add_to_registry, remove_from_registry
from analyzer import analyze_path
from searcher import ask_ai

# Common styling
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

def get_system_language():
    try:
        windll = ctypes.windll.kernel32
        lang_id = windll.GetUserDefaultUILanguage()
        lang_code = locale.windows_locale.get(lang_id, 'en_US')
        if lang_code.startswith('ru'):
            return 'ru', 'Russian'
        else:
            # Fallback for UI is English, but we tell AI to use the system language code
            return 'en', lang_code
    except Exception:
        return 'en', 'English'

LANG_CODE, FULL_LANG_NAME = get_system_language()

# Localization dictionaries
T = {
    'ru': {
        'settings_title': "ЧЗХ? - Настройки",
        'settings_header': "Управление 'ЧЗХ?' в меню ПКМ",
        'add_pkm': "Добавить 'ЧЗХ?' в меню ПКМ",
        'remove_pkm': "Удалить из меню ПКМ",
        'test_btn': "Протестировать на файле",
        'added_success': "Успешно добавлено!",
        'remove_success': "Успешно удалено!",
        'add_err': "Ошибка добавления",
        'remove_err': "Ошибка удаления",

        'app_name': "ЧЗХ?",
        'analyzing': "Анализ...",
        'wait': "Ожидайте...",
        'wait_ai': "Ожидание ответа...",
        'error': "Ошибка",
        'size': "Размер",
        'created': "Дата создания",
        'modified': "Последнее изменение",
        'days_ago': "дней назад",
        'top5': "Топ-5 файлов",
        'pe_meta': "Метаданные (PE)",

        'btn_google': "Искать в Google",
        'btn_vt': "Проверить на VirusTotal",
        'btn_retry': "Повторить",
        'net_err': "Не удалось получить ответ. Проверьте подключение к сети.",
    },
    'en': {
        'settings_title': "WTF? - Settings",
        'settings_header': "Manage 'WTF?' Context Menu",
        'add_pkm': "Add to Context Menu",
        'remove_pkm': "Remove from Context Menu",
        'test_btn': "Test on file",
        'added_success': "Added successfully!",
        'remove_success': "Removed successfully!",
        'add_err': "Error adding",
        'remove_err': "Error removing",

        'app_name': "WTF?",
        'analyzing': "Analyzing...",
        'wait': "Please wait...",
        'wait_ai': "Waiting for response...",
        'error': "Error",
        'size': "Size",
        'created': "Created",
        'modified': "Last modified",
        'days_ago': "days ago",
        'top5': "Top-5 files",
        'pe_meta': "PE Metadata",

        'btn_google': "Search in Google",
        'btn_vt': "Check on VirusTotal",
        'btn_retry': "Retry",
        'net_err': "Failed to get response. Check your network connection.",
    }
}

def clean_markdown(text):
    text = text.replace('**', '')
    text = text.replace('##', '')
    text = text.replace('*', '')
    return text

class SettingsWindow(ctk.CTk):
    def __init__(self, exe_path):
        super().__init__()
        self.exe_path = exe_path
        self.title(T[LANG_CODE]['settings_title'])
        self.geometry("400x300")
        self.resizable(False, False)

        self.grid_columnconfigure(0, weight=1)

        label = ctk.CTkLabel(self, text=T[LANG_CODE]['settings_header'], font=ctk.CTkFont(size=20, weight="bold"))
        label.grid(row=0, column=0, pady=(20, 10))

        self.btn_add = ctk.CTkButton(self, text=T[LANG_CODE]['add_pkm'], command=self.add_reg, height=40)
        self.btn_add.grid(row=1, column=0, pady=10, padx=20, sticky="ew")

        self.btn_remove = ctk.CTkButton(self, text=T[LANG_CODE]['remove_pkm'], command=self.remove_reg, height=40, fg_color="red", hover_color="darkred")
        self.btn_remove.grid(row=2, column=0, pady=10, padx=20, sticky="ew")

        self.status_label = ctk.CTkLabel(self, text="", text_color="gray")
        self.status_label.grid(row=3, column=0, pady=10)

        # Test field
        self.test_frame = ctk.CTkFrame(self)
        self.test_frame.grid(row=4, column=0, pady=10, padx=20, sticky="ew")
        self.test_frame.grid_columnconfigure(0, weight=1)

        self.test_btn = ctk.CTkButton(self.test_frame, text=T[LANG_CODE]['test_btn'], command=self.test_file)
        self.test_btn.grid(row=0, column=0, pady=10, padx=10, sticky="ew")

    def add_reg(self):
        if add_to_registry(self.exe_path):
            self.status_label.configure(text=T[LANG_CODE]['added_success'], text_color="green")
        else:
            self.status_label.configure(text=T[LANG_CODE]['add_err'], text_color="red")

    def remove_reg(self):
        if remove_from_registry():
            self.status_label.configure(text=T[LANG_CODE]['remove_success'], text_color="green")
        else:
            self.status_label.configure(text=T[LANG_CODE]['remove_err'], text_color="red")

    def test_file(self):
        from tkinter import filedialog
        filepath = filedialog.askopenfilename()
        if filepath:
            self.destroy()
            show_popup(filepath)

class PopupWindow(ctk.CTk):
    def __init__(self, target_path):
        super().__init__()
        self.target_path = target_path
        self.title(T[LANG_CODE]['app_name'])
        self.geometry("520x600")

        # Position near mouse cursor
        x = self.winfo_pointerx()
        y = self.winfo_pointery()
        self.geometry(f"+{x+10}+{y+10}")

        # Focus Management
        self.lift()
        self.focus_force()
        self.attributes('-topmost', True)
        self.after(500, lambda: self.attributes('-topmost', False))

        self.bind("<FocusOut>", self.on_focus_out)
        self.bind("<Escape>", lambda e: self.destroy())

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header Info
        self.info_frame = ctk.CTkFrame(self)
        self.info_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        self.name_label = ctk.CTkLabel(self.info_frame, text=T[LANG_CODE]['analyzing'], font=ctk.CTkFont(size=16, weight="bold"))
        self.name_label.pack(anchor="w", padx=10, pady=5)

        self.details_label = ctk.CTkLabel(self.info_frame, text=T[LANG_CODE]['wait'], justify="left")
        self.details_label.pack(anchor="w", padx=10, pady=5)

        # Main AI Text Area
        self.text_area = ctk.CTkTextbox(self, font=ctk.CTkFont(size=14), wrap="word")
        self.text_area.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.text_area.insert("0.0", T[LANG_CODE]['wait_ai'])
        self.text_area.configure(state="disabled")

        # Buttons Frame
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))
        self.btn_frame.grid_columnconfigure(0, weight=1)
        self.btn_frame.grid_columnconfigure(1, weight=1)
        self.btn_frame.grid_columnconfigure(2, weight=1)

        self.btn_google = ctk.CTkButton(self.btn_frame, text=T[LANG_CODE]['btn_google'], state="disabled")
        self.btn_google.grid(row=0, column=0, padx=5)

        self.btn_vt = ctk.CTkButton(self.btn_frame, text=T[LANG_CODE]['btn_vt'], state="disabled")
        self.btn_vt.grid(row=0, column=1, padx=5)

        self.btn_retry = ctk.CTkButton(self.btn_frame, text=T[LANG_CODE]['btn_retry'], command=self.retry_analysis)
        self.btn_retry.grid(row=0, column=2, padx=5)
        self.btn_retry.grid_remove() # Hide initially

        self.sha256 = None
        self.search_query = None

        # Start analysis thread
        self.start_analysis_thread()

    def on_focus_out(self, event):
        def check_focus():
            if self.focus_get() is None:
                self.destroy()
        self.after(100, check_focus)

    def start_analysis_thread(self):
        self.btn_retry.grid_remove()
        self.text_area.configure(state="normal")
        self.text_area.delete("0.0", "end")
        self.text_area.insert("0.0", T[LANG_CODE]['wait_ai'])
        self.text_area.configure(state="disabled")
        threading.Thread(target=self.run_analysis, daemon=True).start()

    def retry_analysis(self):
        self.start_analysis_thread()

    def run_analysis(self):
        # 1. Local Analysis
        analysis = analyze_path(self.target_path)
        if "error" in analysis:
            self.after(0, self.update_error, analysis["error"])
            return

        self.search_query = analysis.get("search_query", "")
        self.sha256 = analysis.get("sha256")

        # Update UI with local info
        self.after(0, self.update_info, analysis)

        # 2. Prepare AI prompt
        name = analysis.get("name", "")
        size = analysis.get("size", "")
        days = analysis.get("days_since_mod", "")

        prompt = (f"You are a built-in Windows utility. Provide an explanation in 3 short bullet points (no fluff, no greetings). "
                  f"The explanation must be provided exactly in this language: {FULL_LANG_NAME}.\n"
                  f"Format the output strictly as:\n"
                  f"1. ЧТО ЭТО / WHAT IS IT (what program or folder it is, and what it's for, considering contents).\n"
                  f"2. ЧТО ВНУТРИ / WHAT IS INSIDE (brief summary of large files and how long ago it was used).\n"
                  f"3. ВЕРДИКТ / VERDICT (is it safe to delete and what will happen).\n\n"
                  f"Object Data:\n"
                  f"Name: {name}\n"
                  f"Size: {size}\n"
                  f"Modified: {days} days ago\n"
                  f"Context Path: {self.search_query}\n")

        if analysis.get("is_dir"):
            prompt += "Top-5 files inside:\n"
            for f in analysis.get("top_files", []):
                prompt += f"- {f['name']} ({f['size']})\n"
        else:
            pe_meta = analysis.get("pe_metadata", {})
            if pe_meta:
                prompt += "PE Metadata:\n"
                for k, v in pe_meta.items():
                    if k in ["ProductName", "CompanyName", "FileDescription"]:
                        prompt += f"- {k}: {v}\n"

        # 3. Query AI
        success, ai_response = ask_ai(prompt)
        if success:
            cleaned_response = clean_markdown(ai_response)
            self.after(0, self.update_ai_response, cleaned_response)
        else:
            self.after(0, self.show_network_error)

    def show_network_error(self):
        self.text_area.configure(state="normal")
        self.text_area.delete("0.0", "end")
        self.text_area.insert("0.0", T[LANG_CODE]['net_err'])
        self.text_area.configure(state="disabled")
        self.btn_retry.grid()

    def update_error(self, err_msg):
        self.name_label.configure(text=T[LANG_CODE]['error'])
        self.details_label.configure(text=err_msg)

    def update_info(self, analysis):
        self.name_label.configure(text=analysis["name"])

        details = f"{T[LANG_CODE]['size']}: {analysis.get('size', 'N/A')}\n"
        details += f"{T[LANG_CODE]['created']}: {analysis.get('creation_date', 'N/A')}\n"
        details += f"{T[LANG_CODE]['modified']}: {analysis.get('days_since_mod', 'N/A')} {T[LANG_CODE]['days_ago']}\n"

        if analysis.get("is_dir"):
            details += f"\n{T[LANG_CODE]['top5']}:\n"
            for f in analysis.get("top_files", []):
                details += f" - {f['name']} ({f['size']})\n"
        else:
            pe_meta = analysis.get("pe_metadata", {})
            if pe_meta:
                details += f"\n{T[LANG_CODE]['pe_meta']}:\n"
                for k in ["ProductName", "CompanyName", "FileDescription"]:
                    if k in pe_meta:
                        details += f" - {k}: {pe_meta[k]}\n"

        self.details_label.configure(text=details)

        # Enable Buttons
        if self.search_query:
            self.btn_google.configure(state="normal", command=lambda: webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote(self.search_query)}"))
        if self.sha256:
            self.btn_vt.configure(state="normal", command=lambda: webbrowser.open(f"https://www.virustotal.com/gui/file/{self.sha256}"))

    def update_ai_response(self, text):
        self.text_area.configure(state="normal")
        self.text_area.delete("0.0", "end")
        self.text_area.insert("0.0", text)
        self.text_area.configure(state="disabled")

def show_settings(exe_path):
    app = SettingsWindow(exe_path)
    app.mainloop()

def show_popup(target_path):
    app = PopupWindow(target_path)
    app.mainloop()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        show_popup(sys.argv[1])
    else:
        show_settings(sys.executable)
