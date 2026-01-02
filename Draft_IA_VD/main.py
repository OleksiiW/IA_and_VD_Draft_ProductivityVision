import os
import sys
import customtkinter as ctk
from tkinter import messagebox
from config import Config
from engine import ProductivityEngine
from views import Sidebar, DashboardView, ChartAnalysisView, RecommendationWindow, AddEmployeeWindow


class App(ctk.CTk):
    """
    Головний клас застосунку, що успадковує функціонал customtkinter.
    Відповідає за ініціалізацію головного вікна, налаштування шляхів,
    підключення логічного рушія та керування навігацією між екранами.
    """
    def __init__(self):
        """
        Конструктор класу. Налаштовує тему, геометрію вікна, іконку,
        визначає шляхи до файлів (враховуючи скомпільований стан),
        ініціалізує рушій даних та створює основні елементи інтерфейсу (Sidebar, Main Area).
        """
        super().__init__()
        ctk.set_appearance_mode(Config.THEME_MODE)
        ctk.set_default_color_theme(Config.COLOR_THEME)
        self.title(Config.APP_NAME)
        self.geometry(Config.GEOMETRY)

        if os.path.exists(Config.ICON_PATH):
            try:
                self.iconbitmap(Config.ICON_PATH)
            except Exception:
                pass

        if getattr(sys, 'frozen', False):
            app_path = os.path.dirname(sys.executable)
        else:
            app_path = os.path.dirname(os.path.abspath(__file__))

        self.engine = ProductivityEngine(app_path)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = Sidebar(self, self)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        self.main_area = ctk.CTkFrame(self, fg_color="transparent")
        self.main_area.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        self.view_dashboard = DashboardView(self.main_area, self.engine)
        self.view_charts = ChartAnalysisView(self.main_area, self.engine)

        self._start_application()

    def _start_application(self):
        """
        Завантажує ресурси (дані та моделі ML) через екземпляр ProductivityEngine.
        У разі успіху відображає дашборд, інакше показує повідомлення про критичну помилку.
        """
        try:
            self.engine.load_resources()
            self.show_dashboard()
        except Exception as e:
            messagebox.showerror("Critical Error", f"Failed to initialize:\n{e}")

    def show_dashboard(self):
        """
        Приховує екран графіків та відображає екран дашборду (таблиці).
        Оновлює дані у таблиці при переключенні.
        """
        self.view_charts.pack_forget()
        self.view_dashboard.pack(fill="both", expand=True)
        self.view_dashboard.refresh_data()

    def show_charts(self):
        """
        Приховує екран дашборду та відображає екран з графіками.
        Ініціює побудову графіків, якщо вони ще не були побудовані або потребують оновлення.
        """
        self.view_dashboard.pack_forget()
        self.view_charts.pack(fill="both", expand=True)
        self.view_charts.draw_charts()

    def open_recommendation_window(self):
        """
        Створює та відкриває окреме модальне вікно для отримання ML-рекомендацій
        щодо обраного співробітника.
        """
        RecommendationWindow(self, self.engine)

    def open_add_employee_window(self):
        """
        Створює та відкриває окреме модальне вікно для додавання нового співробітника.
        Передає callback-функцію для оновлення інтерфейсу після закриття вікна.
        """
        AddEmployeeWindow(self, self.engine, on_close_callback=self.refresh_all_views)

    def refresh_all_views(self):
        """
        Оновлює дані у всіх компонентах інтерфейсу (таблиця та графіки).
        Скидає прапорець побудови графіків, щоб змусити їх перемалюватися з новими даними.
        """
        self.view_dashboard.refresh_data()
        self.view_charts.charts_drawn = False
        if self.view_charts.winfo_ismapped():
            self.view_charts.draw_charts()


if __name__ == "__main__":
    app = App()
    app.mainloop()

# pyinstaller --noconsole --onefile --collect-all xgboost main.py
# pyinstaller --noconsole --onefile --name "Productivity Vision" --icon "Data/icon_PV.ico" --collect-all xgboost main.py
