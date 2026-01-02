import tkinter as tk
import customtkinter as ctk


class CircularProgress(ctk.CTkFrame):
    """
    Клас, що реалізує віджет кругового прогрес-бару.
    Спадкується від CTkFrame та використовує стандартний Canvas для візуалізації.
    """
    def __init__(self, master, size=150, font_size=20, title="", **kwargs):
        """
        Ініціалізує віджет, встановлює розміри полотна та налаштовує текстовий заголовок, якщо він переданий.
        """
        super().__init__(master, fg_color="transparent", **kwargs)
        self.size = size
        self.font_size = font_size
        self.title = title

        self.canvas = tk.Canvas(self, width=size, height=size, bg="#2b2b2b", highlightthickness=0)
        self.canvas.pack()

        if title:
            self.lbl_title = ctk.CTkLabel(self, text=title, font=("Arial", 12, "bold"))
            self.lbl_title.pack(pady=5)

    def set_value(self, value: float, color: str):
        """
        Оновлює візуальне відображення прогресу: очищає полотно, малює фонове кільце,
        активну дугу відповідно до відсотка та текстове значення по центру.
        """
        self.canvas.delete("all")
        x0, y0 = 10, 10
        x1, y1 = self.size - 10, self.size - 10
        self.canvas.create_oval(x0, y0, x1, y1, outline="#404040", width=10)
        extent = -360 * (value / 100)
        self.canvas.create_arc(x0, y0, x1, y1, start=90, extent=extent,
                               style="arc", outline=color, width=10)
        self.canvas.create_text(self.size / 2, self.size / 2, text=f"{value:.1f}%",
                                fill="white", font=("Arial", self.font_size, "bold"))
