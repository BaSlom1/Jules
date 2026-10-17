import sys
import threading
import webbrowser
import urllib.parse
try:
    import customtkinter as ctk
except ImportError:
    import tkinter as ctk

from registry_manager import add_to_registry, remove_from_registry
from analyzer import analyze_path
from searcher import search

# Common styling
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class SettingsWindow(ctk.CTk):
    def __init__(self, exe_path):
        super().__init__()
        self.exe_path = exe_path
        self.title("ЧЗХ? - Настройки")
        self.geometry("400x300")
        self.resizable(False, False)

        self.grid_columnconfigure(0, weight=1)

        label = ctk.CTkLabel(self, text="Управление 'ЧЗХ?' в меню ПКМ", font=ctk.CTkFont(size=20, weight="bold"))
        label.grid(row=0, column=0, pady=(20, 10))

        self.btn_add = ctk.CTkButton(self, text="Добавить 'ЧЗХ?' в меню ПКМ", command=self.add_reg, height=40)
        self.btn_add.grid(row=1, column=0, pady=10, padx=20, sticky="ew")

        self.btn_remove = ctk.CTkButton(self, text="Удалить из меню ПКМ", command=self.remove_reg, height=40, fg_color="red", hover_color="darkred")
        self.btn_remove.grid(row=2, column=0, pady=10, padx=20, sticky="ew")

        self.status_label = ctk.CTkLabel(self, text="", text_color="gray")
        self.status_label.grid(row=3, column=0, pady=10)

        # Test field
        self.test_frame = ctk.CTkFrame(self)
        self.test_frame.grid(row=4, column=0, pady=10, padx=20, sticky="ew")
        self.test_frame.grid_columnconfigure(0, weight=1)

        self.test_btn = ctk.CTkButton(self.test_frame, text="Протестировать на файле", command=self.test_file)
        self.test_btn.grid(row=0, column=0, pady=10, padx=10, sticky="ew")

    def add_reg(self):
        if add_to_registry(self.exe_path):
            self.status_label.configure(text="Успешно добавлено!", text_color="green")
        else:
            self.status_label.configure(text="Ошибка добавления", text_color="red")

    def remove_reg(self):
        if remove_from_registry():
            self.status_label.configure(text="Успешно удалено!", text_color="green")
        else:
            self.status_label.configure(text="Ошибка удаления", text_color="red")

    def test_file(self):
        from tkinter import filedialog
        filepath = filedialog.askopenfilename()
        if filepath:
            self.destroy()
            show_popup(filepath)

class ResultCard(ctk.CTkFrame):
    def __init__(self, master, title, body, href, **kwargs):
        super().__init__(master, **kwargs)
        self.href = href

        # Make the title a clickable link
        self.title_label = ctk.CTkLabel(self, text=title, font=ctk.CTkFont(size=14, weight="bold"), text_color="#5ea8ff", cursor="hand2", anchor="w", justify="left", wraplength=400)
        self.title_label.pack(anchor="w", padx=10, pady=(10, 0))
        self.title_label.bind("<Button-1>", lambda e: webbrowser.open(self.href))

        self.body_label = ctk.CTkLabel(self, text=body, anchor="w", justify="left", wraplength=400)
        self.body_label.pack(anchor="w", padx=10, pady=(5, 10))

class PopupWindow(ctk.CTk):
    def __init__(self, target_path):
        super().__init__()
        self.target_path = target_path
        self.title("ЧЗХ?")
        self.geometry("480x550")

        # Position near mouse cursor
        x = self.winfo_pointerx()
        y = self.winfo_pointery()
        self.geometry(f"+{x+10}+{y+10}")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header Info
        self.info_frame = ctk.CTkFrame(self)
        self.info_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        self.name_label = ctk.CTkLabel(self.info_frame, text="Анализ...", font=ctk.CTkFont(size=16, weight="bold"))
        self.name_label.pack(anchor="w", padx=10, pady=5)

        self.details_label = ctk.CTkLabel(self.info_frame, text="Ожидайте...", justify="left")
        self.details_label.pack(anchor="w", padx=10, pady=5)

        # Scrollable Search Results
        self.results_frame = ctk.CTkScrollableFrame(self)
        self.results_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        # Buttons Frame
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))
        self.btn_frame.grid_columnconfigure(0, weight=1)
        self.btn_frame.grid_columnconfigure(1, weight=1)

        self.btn_google = ctk.CTkButton(self.btn_frame, text="Открыть в Google", state="disabled")
        self.btn_google.grid(row=0, column=0, padx=5)

        self.btn_vt = ctk.CTkButton(self.btn_frame, text="Проверить на VirusTotal", state="disabled")
        self.btn_vt.grid(row=0, column=1, padx=5)

        self.sha256 = None
        self.search_query = None

        # Start analysis thread
        threading.Thread(target=self.run_analysis, daemon=True).start()

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

        # 2. Search
        if self.search_query:
            results = search(self.search_query)
            self.after(0, self.update_results, results)
        else:
            self.after(0, self.update_results_empty)

    def update_error(self, err_msg):
        self.name_label.configure(text="Ошибка")
        self.details_label.configure(text=err_msg)

    def update_info(self, analysis):
        self.name_label.configure(text=analysis["name"])

        details = f"Размер: {analysis.get('size', 'N/A')}\n"
        details += f"Дата создания: {analysis.get('creation_date', 'N/A')}\n"
        details += f"Последнее изменение: {analysis.get('days_since_mod', 'N/A')} дней назад\n"

        if analysis.get("is_dir"):
            details += "\nТоп-5 файлов:\n"
            for f in analysis.get("top_files", []):
                details += f" - {f['name']} ({f['size']})\n"
        else:
            pe_meta = analysis.get("pe_metadata", {})
            if pe_meta:
                details += "\nМетаданные (PE):\n"
                for k in ["ProductName", "CompanyName", "FileDescription"]:
                    if k in pe_meta:
                        details += f" - {k}: {pe_meta[k]}\n"

        self.details_label.configure(text=details)

        # Enable Buttons
        if self.search_query:
            self.btn_google.configure(state="normal", command=lambda: webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote(self.search_query)}"))
        if self.sha256:
            self.btn_vt.configure(state="normal", command=lambda: webbrowser.open(f"https://www.virustotal.com/gui/file/{self.sha256}"))

    def update_results(self, results):
        # Clear existing
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        if not results:
            ctk.CTkLabel(self.results_frame, text="Ничего не найдено").pack(pady=20)
            return

        for r in results:
            card = ResultCard(self.results_frame, title=r["title"], body=r["body"], href=r["href"])
            card.pack(fill="x", pady=5)

    def update_results_empty(self):
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        ctk.CTkLabel(self.results_frame, text="Не удалось сформировать поисковый запрос").pack(pady=20)


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
