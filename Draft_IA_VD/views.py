import customtkinter as ctk
import pandas as pd
import numpy as np
from tkinter import ttk, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from config import Config
from ui_widgets import CircularProgress
from charts import ChartBuilder
from engine import ProductivityEngine


class Sidebar(ctk.CTkFrame):
    """
    Клас бічної панелі навігації.
    Відповідає за відображення логотипу та кнопок перемикання між основними
    екранами програми: Дашборд, Графіки, Рекомендації, Додавання співробітника.
    """
    def __init__(self, master, app_instance, **kwargs):
        super().__init__(master, width=200, corner_radius=0, **kwargs)
        self.app = app_instance
        self.logo = ctk.CTkLabel(self, text="Productivity\nVision\n(Beta)", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo.pack(pady=(20, 10))

        self.btn_dash = self._create_btn("Дашборд", command=self.app.show_dashboard)
        self.btn_charts = self._create_btn("Графіки (Charts)", command=self.app.show_charts, color=Config.COLOR_MED)
        self.btn_rec = self._create_btn("Рекомендації (ML)", command=self.app.open_recommendation_window)
        self.btn_add = self._create_btn("Додати співробітника", command=self.app.open_add_employee_window, color="#333")

        ctk.CTkLabel(self, text="v1.0 Beta", text_color="gray").pack(side="bottom", pady=10)

    def _create_btn(self, text, command=None, state="normal", color=None):
        """
        Допоміжний метод для створення стандартизованих кнопок меню.
        """
        btn = ctk.CTkButton(self, text=text, command=command, state=state)
        if color: btn.configure(fg_color=color, hover_color="#C97A1E")
        btn.pack(pady=10, padx=20)
        return btn


class RecommendationWindow(ctk.CTkToplevel):
    """
    Окреме вікно для детального аналізу конкретного співробітника.
    Включає пошук за ID, візуалізацію метрик продуктивності
    та генерацію ML-рекомендацій для покращення показників.
    """
    def __init__(self, parent, engine: ProductivityEngine):
        super().__init__(parent)
        self.engine = engine
        self.title("ML Recommendation System")
        self.geometry("950x850")
        self.attributes("-topmost", True)
        self.current_emp_id = None
        self._setup_ui()

    def _setup_ui(self):
        """
        Ініціалізує графічний інтерфейс вікна: панель пошуку
        та контейнер для відображення результатів.
        """
        ctk.CTkLabel(self, text="Прогнозування та Аналіз", font=("Arial", 20, "bold")).pack(pady=(20, 10))
        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.pack(pady=10)
        ctk.CTkLabel(search_frame, text="Employee ID:", font=("Arial", 14)).pack(side="left", padx=10)
        self.search_entry = ctk.CTkEntry(search_frame, width=150, font=("Arial", 14))
        self.search_entry.insert(0, "EMP")
        self.search_entry.pack(side="left", padx=10)
        ctk.CTkButton(search_frame, text="Знайти", command=self._perform_search).pack(side="left", padx=10)

        self.content_frame = ctk.CTkScrollableFrame(self, label_text="Результати аналізу")
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=10)
        self.placeholder_lbl = ctk.CTkLabel(self.content_frame, text="Введіть ID співробітника.")
        self.placeholder_lbl.pack(pady=50)

    def _perform_search(self):
        """
        Виконує пошук співробітника в базі даних за введеним ID.
        Оновлює інтерфейс залежно від результату пошуку.
        """
        emp_id = self.search_entry.get().strip()
        if not emp_id: return
        data = self.engine.find_employee(emp_id)
        for widget in self.content_frame.winfo_children(): widget.destroy()
        if data is None:
            ctk.CTkLabel(self.content_frame, text=f"Співробітника {emp_id} не знайдено.", text_color="red").pack(
                pady=20)
            return
        self.current_emp_id = emp_id
        self._build_analysis_view(data)

    def _build_analysis_view(self, data):
        """
        Будує детальне представлення даних співробітника:
        основний показник продуктивності, кнопку для HR-метрик,
        кнопку запиту до AI та таблицю з характеристиками.
        """
        score = data['Productivity_Score']
        color = Config.COLOR_HIGH if score > 75 else Config.COLOR_MED if score > 45 else Config.COLOR_LOW

        top_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        top_frame.pack(pady=20)
        ctk.CTkLabel(top_frame, text=f"Аналіз для: {data['Employee_ID']}", font=("Arial", 16)).pack(pady=5)
        self.big_prog = CircularProgress(top_frame, size=220, font_size=32)
        self.big_prog.pack(pady=15)
        self.big_prog.set_value(score, color)

        self.btn_reveal_hr = ctk.CTkButton(self.content_frame, text="Побачити оцінки HR ⬇", width=200,
                                           command=lambda: self._show_hr_metrics(data))
        self.btn_reveal_hr.pack(pady=10)
        self.hr_metrics_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")

        self.btn_get_rec = ctk.CTkButton(self.content_frame, text="Отримати рекомендації AI 🤖",
                                         font=("Arial", 18, "bold"), height=50, fg_color=Config.COLOR_HIGH,
                                         command=self._on_get_recommendations)
        self.btn_get_rec.pack(fill="x", padx=40, pady=20)
        self.rec_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.rec_frame.pack(fill="x", pady=10)

        ttk.Separator(self.content_frame, orient='horizontal').pack(fill='x', pady=20)
        details_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        details_frame.pack(fill="x", padx=10)
        exclude = ["Employee_ID", "Productivity_Score", "Efficiency_Rating", "Quality_Score", "Task_Completion_Rate",
                   "Innovation_Score"]
        r, c = 0, 0
        for k, v in data.items():
            if k in exclude: continue
            val = f"{v:.3f}" if isinstance(v, (float, np.floating)) else str(v)
            card = ctk.CTkFrame(details_frame, border_width=1, border_color="#444")
            card.grid(row=r, column=c, sticky="ew", padx=5, pady=5)
            ctk.CTkLabel(card, text=k, font=("Arial", 11, "bold"), text_color="gray").pack(anchor="w", padx=5)
            ctk.CTkLabel(card, text=val, font=("Arial", 13)).pack(anchor="w", padx=5)
            c += 1
            if c >= 2: c = 0; r += 1
        details_frame.grid_columnconfigure(0, weight=1);
        details_frame.grid_columnconfigure(1, weight=1)

    def _show_hr_metrics(self, data):
        """
        Розкриває приховану панель з додатковими HR-метриками
        (Ефективність, Якість, Інноваційність тощо).
        """
        self.btn_reveal_hr.pack_forget()
        self.hr_metrics_frame.pack(fill="x", pady=10, after=self.big_prog.master)
        metrics = [("Efficiency_Rating", "Efficiency"), ("Quality_Score", "Quality"),
                   ("Task_Completion_Rate", "Task Rate"), ("Innovation_Score", "Innovation")]
        cont = ctk.CTkFrame(self.hr_metrics_frame, fg_color="transparent")
        cont.pack()
        for i, (k, lbl) in enumerate(metrics):
            val = data.get(k, 0)
            col = Config.COLOR_HIGH if val > 75 else Config.COLOR_MED if val > 45 else Config.COLOR_LOW
            fr = ctk.CTkFrame(cont, fg_color="transparent")
            fr.grid(row=0, column=i, padx=10)
            cp = CircularProgress(fr, size=90, font_size=14, title=lbl)
            cp.pack();
            cp.set_value(val, col)

    def _on_get_recommendations(self):
        """
        Запитує у ML-двигуна рекомендації для поточного співробітника
        та відображає їх у вигляді карток стратегій.
        """
        if not self.current_emp_id: return
        df_rec = self.engine.get_recommendations(self.current_emp_id)
        for w in self.rec_frame.winfo_children(): w.destroy()
        if df_rec.empty:
            ctk.CTkLabel(self.rec_frame, text="Немає рекомендацій.", text_color="yellow").pack()
            return

        ctk.CTkLabel(self.rec_frame, text="ТОП-3 Стратегії:", font=("Arial", 16, "bold")).pack(pady=10)
        for idx, row in df_rec.head(3).iterrows():
            card = ctk.CTkFrame(self.rec_frame, border_width=2, border_color=Config.COLOR_HIGH)
            card.pack(fill="x", padx=10, pady=5)
            left = ctk.CTkFrame(card, fg_color="transparent")
            left.pack(side="left", padx=10, pady=10, fill="x", expand=True)
            ctk.CTkLabel(left, text=row['Дія'], font=("Arial", 16, "bold"), text_color="white").pack(anchor="w")
            ctk.CTkLabel(left, text=f"Параметр: {row['Ознака']} ({row['Поточне']} ➝ {row['Рекомендація']})",
                         font=("Arial", 12), text_color="gray").pack(anchor="w")
            ctk.CTkLabel(left, text=f"💡 {row['Порада']}", font=("Arial", 13, "italic"), text_color="#FFD54F",
                         wraplength=450, justify="left").pack(anchor="w")
            right = ctk.CTkFrame(card, fg_color="transparent")
            right.pack(side="right", padx=20)
            ctk.CTkLabel(right, text=f"+{row['Приріст (%)']:.2f}%", font=("Arial", 20, "bold"),
                         text_color=Config.COLOR_HIGH).pack()


class DashboardView(ctk.CTkFrame):
    """
    Головний екран програми (Дашборд).
    Відображає таблицю зі списком співробітників, панель фільтрації,
    сортування та пошуку.
    """
    def __init__(self, master, engine: ProductivityEngine):
        super().__init__(master, fg_color="transparent")
        self.engine = engine
        self._setup_top_panel()
        self._setup_table()

    def _setup_top_panel(self):
        """
        Налаштовує верхню панель керування: пошук, випадаючі списки
        для ліміту записів та параметрів сортування.
        """
        panel = ctk.CTkFrame(self, fg_color="transparent")
        panel.pack(fill="x", pady=(0, 10))
        left = ctk.CTkFrame(panel, fg_color="transparent")
        left.pack(side="left")
        ctk.CTkLabel(left, text="Пошук (ID):", font=("Arial", 12, "bold")).pack(side="left", padx=5)
        self.search_entry = ctk.CTkEntry(left, placeholder_text="EMP001", width=120)
        self.search_entry.pack(side="left", padx=5)
        ctk.CTkButton(left, text="Знайти", width=80, command=self._on_search).pack(side="left", padx=5)

        right = ctk.CTkFrame(panel, fg_color="transparent")
        right.pack(side="right")
        self.combo_limit = ctk.CTkComboBox(right, values=["10", "30", "50", "100", "All"], width=70,
                                           command=lambda x: self.refresh_data())
        self.combo_limit.set("10");
        self.combo_limit.pack(side="left", padx=5)
        self.combo_sort = ctk.CTkComboBox(right, values=Config.SORT_OPTIONS, width=160,
                                          command=lambda x: self.refresh_data())
        self.combo_sort.set("Productivity_Score");
        self.combo_sort.pack(side="left", padx=5)
        self.combo_order = ctk.CTkComboBox(right, values=["Спадання", "Зростання", "Випадково"], width=110,
                                           command=lambda x: self.refresh_data())
        self.combo_order.set("Спадання");
        self.combo_order.pack(side="left", padx=5)

    def _setup_table(self):
        """
        Ініціалізує віджет Treeview для відображення табличних даних
        зі смугами прокрутки.
        """
        container = ctk.CTkFrame(self)
        container.pack(fill="both", expand=True, pady=10)
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", rowheight=25)
        style.configure("Treeview.Heading", background="#1f6aa5", foreground="white", font=('Arial', 10, 'bold'))
        style.map("Treeview", background=[('selected', '#1f538d')])

        ysb = ttk.Scrollbar(container, orient="vertical");
        xsb = ttk.Scrollbar(container, orient="horizontal")
        self.tree = ttk.Treeview(container, show="headings", yscrollcommand=ysb.set, xscrollcommand=xsb.set,
                                 selectmode="extended")
        ysb.config(command=self.tree.yview);
        xsb.config(command=self.tree.xview)
        self.tree.grid(row=0, column=0, sticky="nsew")
        ysb.grid(row=0, column=1, sticky="ns");
        xsb.grid(row=1, column=0, sticky="ew")
        container.grid_rowconfigure(0, weight=1);
        container.grid_columnconfigure(0, weight=1)
        self.tree.bind("<Control-c>", self._copy_selection)

    def refresh_data(self):
        """
        Завантажує дані з двигуна відповідно до обраних фільтрів
        та оновлює вміст таблиці.
        """
        df = self.engine.get_data(self.combo_sort.get(),
                                  len(self.engine.df_full) if self.combo_limit.get() == "All" else int(
                                      self.combo_limit.get()),
                                  self.combo_order.get())
        if df.empty: return
        self.tree.delete(*self.tree.get_children())
        cols = list(df.columns)
        if 'Productivity_Score' in cols: cols.insert(0, cols.pop(cols.index('Productivity_Score')))
        self.tree["columns"] = cols
        for col in cols:
            self.tree.heading(col, text=col)
            width = 90 if col == "Employee_ID" else (130 if col == "Productivity_Score" else 120)
            self.tree.column(col, width=width, minwidth=80, stretch=False, anchor="center")
        for _, row in df.iterrows():
            vals = [f"{x:.3f}" if isinstance(x, (float, np.floating)) else x for x in row[cols]]
            self.tree.insert("", "end", values=vals)

    def _on_search(self):
        """
        Обробляє подію пошуку: відкриває картку співробітника, якщо знайдено,
        або показує повідомлення про помилку.
        """
        emp_id = self.search_entry.get().strip()
        data = self.engine.find_employee(emp_id)
        if data is not None:
            EmployeeCardWindow(self, data)
        else:
            messagebox.showinfo("Результат", f"Співробітника {emp_id} не знайдено.")

    def _copy_selection(self, event):
        """
        Копіює виділені рядки таблиці у буфер обміну.
        """
        selected = self.tree.selection()
        text = ""
        for item in selected: text += "\t".join(map(str, self.tree.item(item, 'values'))) + "\n"
        self.clipboard_clear();
        self.clipboard_append(text);
        self.update()


class EmployeeCardWindow(ctk.CTkToplevel):
    """
    Просте модальне вікно для відображення короткої інформації
    про співробітника (Картка).
    """
    def __init__(self, parent, data: pd.Series):
        super().__init__(parent)
        self.title(f"Картка: {data['Employee_ID']}")
        self.geometry("450x550")
        self.data = data
        ctk.CTkLabel(self, text="Деталі Співробітника", font=("Arial", 20, "bold")).pack(pady=15)
        score = self.data['Productivity_Score']
        color = Config.COLOR_HIGH if score > 75 else Config.COLOR_MED if score > 45 else Config.COLOR_LOW
        ctk.CTkLabel(self, text=f"{score:.3f}", font=("Arial", 28, "bold"), text_color=color).pack(pady=10)
        info = "".join([f"{k}: {self.data[k]}\n" for k in
                        ["Department", "Job_Level", "Years_Experience", "Job_Satisfaction", "Age"] if k in self.data])
        ctk.CTkLabel(self, text=info, font=("Arial", 14), justify="left").pack(pady=10)


class ChartAnalysisView(ctk.CTkScrollableFrame):
    """
    Сторінка розширеного аналізу графіків (Exploratory Data Analysis).
    Будує та відображає набір діаграм на основі повного датасету.
    """

    def __init__(self, master, engine: ProductivityEngine):
        super().__init__(master, fg_color="transparent", label_text="Розширений Аналіз Графіків")
        self.engine = engine
        self.charts_drawn = False

    def draw_charts(self):
        """
        Генерує та розміщує графіки у сітці, якщо вони ще не були побудовані.
        Використовує ChartBuilder для створення фігур Matplotlib.
        """
        if self.charts_drawn or self.engine.df_full is None:
            return

        df = self.engine.df_full

        r1 = ctk.CTkFrame(self, fg_color="transparent")
        r1.pack(fill="x", pady=10)
        self._add_chart(r1, ChartBuilder.create_3d_donut(df, "Marital_Status", "Marital Status Distribution"))
        self._add_chart(r1, ChartBuilder.create_countplot_horiz(df, "Department", "Department Distribution"))

        r2 = ctk.CTkFrame(self, fg_color="transparent")
        r2.pack(fill="x", pady=10)
        self._add_chart(r2, ChartBuilder.create_countplot_vertical(df, "Stress_Level", "Stress Level Distribution"))
        self._add_chart(r2, ChartBuilder.create_hist_kde(df, "Years_Experience", 25, "Years Experience (Hist+KDE)"))

        r3 = ctk.CTkFrame(self, fg_color="transparent")
        r3.pack(fill="x", pady=10)
        self._add_chart(r3, ChartBuilder.create_hist_kde(df, "Age", 25, "Age Distribution"))
        self._add_chart(r3, ChartBuilder.create_hist_kde(df, "Commute_Time_Minutes", 30, "Commute Time"))

        r4 = ctk.CTkFrame(self, fg_color="transparent")
        r4.pack(fill="x", pady=10)
        self._add_chart(r4, ChartBuilder.create_violin(df, "Job_Satisfaction", "Job Satisfaction (Violin)"))
        self._add_chart(r4,
                        ChartBuilder.create_hist2d(df, "Age", "Years_Experience", 25, "Age vs Experience (2D Hist)"))

        self.charts_drawn = True

    def _add_chart(self, parent, fig):
        """
        Вбудовує фігуру Matplotlib у віджет Tkinter Canvas.
        """
        frame = ctk.CTkFrame(parent)
        frame.pack(side="left", fill="both", expand=True, padx=10)
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)


class AddEmployeeWindow(ctk.CTkToplevel):
    """
    Вікно для додавання нового співробітника.
    Забезпечує введення даних через форму, їх валідацію, збереження
    та миттєвий ML-прогноз продуктивності.
    """
    def __init__(self, parent, engine: ProductivityEngine, on_close_callback=None):
        super().__init__(parent)
        self.engine = engine
        self.on_close_callback = on_close_callback
        self.title("Додати нового співробітника")
        self.geometry("600x800")

        self.entries = {}

        self._setup_ui()

    def _setup_ui(self):
        """
        Створює динамічну форму введення даних на основі списку полів.
        Включає автоматичну генерацію ID та поточної дати.
        """
        title = ctk.CTkLabel(self, text="Новий Співробітник", font=("Arial", 20, "bold"))
        title.pack(pady=10)

        info_frame = ctk.CTkFrame(self)
        info_frame.pack(fill="x", padx=20, pady=5)

        next_id = self.engine.generate_new_id()
        curr_date = pd.Timestamp.now().strftime("%Y-%m-%d")

        ctk.CTkLabel(info_frame, text=f"ID: {next_id}", text_color=Config.COLOR_HIGH, font=("Arial", 14, "bold")).pack(
            side="left", padx=20)
        ctk.CTkLabel(info_frame, text=f"Date: {curr_date}", text_color="gray").pack(side="right", padx=20)

        self.scroll = ctk.CTkScrollableFrame(self, label_text="Дані для ML-моделі")
        self.scroll.pack(fill="both", expand=True, padx=20, pady=10)

        fields = [
            ("Вік (Age)", "Age", "int", None),
            ("Стать (Gender)", "Gender", "combo", ["Male", "Female", "Non-binary"]),
            ("Сімейний стан", "Marital_Status", "combo", ["Single", "Married", "Divorced", "In Relationship"]),
            ("Освіта", "Education_Level", "combo",
             ["High School", "Associate Degree", "Bachelor Degree", "Professional Degree", "Master Degree", "PhD"]),
            ("Наявність дітей", "Has_Children", "combo", ["Yes", "No"]),

            ("Відділ", "Department", "combo", ['Product', 'Customer Success', 'Operations', 'Finance',
             'Engineering', 'HR', 'Marketing', 'Sales', 'Data Science', 'Design']),
            ("Індустрія", "Industry", "combo", ['Finance', 'Education', 'Technology', 'Media', 'Retail',
             'Manufacturing', 'Consulting', 'Government', 'Non-profit', 'Healthcare']),
            ("Рівень посади", "Job_Level", "combo", ["Junior", "Mid-Level", "Senior", "Lead", "Manager", "Director"]),
            ("Досвід (років)", "Years_Experience", "int", None),
            ("Розмір компанії", "Company_Size", "combo",
             ["Startup (1-50)", "Small (51-200)", "Medium (201-1000)", "Large (1001-5000)", "Enterprise (5000+)"]),

            ("Днів вдома (WFH)", "WFH_Days_Per_Week", "int", None),
            ("Годин на тиждень", "Work_Hours_Per_Week", "int", None),
            ("Мітингів на тиждень", "Meetings_Per_Week", "int", None),
            ("Тип локації", "Location_Type", "combo", ["Urban", "Suburban", "Rural"]),
            ("Час в дорозі (хв)", "Commute_Time_Minutes", "int", None),

            ("Якість дом. офісу", "Home_Office_Quality", "combo", ["Poor", "Average", "Good", "Excellent"]),
            ("Інтернет", "Internet_Speed_Category", "combo",
             ["Slow (<25 Mbps)", "Moderate (25-50 Mbps)", "Fast (50-100 Mbps)", "Very Fast (100+ Mbps)"]),

            ("Підтримка менеджера", "Manager_Support_Level", "combo",
             ["Low", "Moderate", "High", "Very Low", "Very High"]),
            ("Колаборація", "Team_Collaboration_Frequency", "combo",
             ["Monthly", "Bi-weekly", "Weekly", "Few times per week", "Daily"]),
            ("Оцінка якості відповідей", 'Response_Quality', 'combo', ['Medium', 'High', 'Low']),

            ("Задоволеність (1-100)", "Job_Satisfaction", "float", None),
            ("Work Life Balance (1-10)", "Work_Life_Balance", "int", None),
            ("Рівень стресу (1-10)", "Stress_Level", "int", None),

            ("Ефективність (1-100)", "Efficiency_Rating", "float", None),
            ("Якість роботи (1-100)", "Quality_Score", "float", None),
            ("Виконання задач (1-100)", "Task_Completion_Rate", "float", None),
            ("Інноваційність (1-100)", "Innovation_Score", "float", None)
        ]

        for label_text, col_name, w_type, options in fields:
            row_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
            row_frame.pack(fill="x", pady=5)

            ctk.CTkLabel(row_frame, text=label_text, width=150, anchor="w").pack(side="left")

            if w_type == "combo":
                widget = ctk.CTkComboBox(row_frame, values=options, width=200)
                if options: widget.set(options[0])
            else:
                widget = ctk.CTkEntry(row_frame, width=200, placeholder_text="0")

            widget.pack(side="right", padx=10)
            self.entries[col_name] = (widget, w_type)

        ctk.CTkButton(self, text="Зберегти та Прогнозувати",
                      fg_color=Config.COLOR_HIGH, height=40,
                      command=self._save).pack(pady=20)

    def _save(self):
        """
        Збирає дані з полів введення, конвертує типи, передає їх у Engine
        для збереження та прогнозування, після чого закриває вікно.
        """
        data = {}
        try:
            for col, (widget, w_type) in self.entries.items():
                val = widget.get()

                if w_type == "int":
                    data[col] = int(val) if val else 0
                elif w_type == "float":
                    data[col] = float(val) if val else 0.0
                else:
                    data[col] = val

            new_id = self.engine.add_new_employee(data)

            messagebox.showinfo("Успіх", f"Співробітника {new_id} додано!\nML Score розраховано.")

            if self.on_close_callback:
                self.on_close_callback()

            self.destroy()

        except ValueError as e:
            messagebox.showerror("Помилка даних", f"Перевірте числові поля.\n{e}")
        except Exception as e:
            messagebox.showerror("Помилка", f"Щось пішло не так:\n{e}")
