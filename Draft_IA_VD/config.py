import os


class Config:
    """
    Центральний клас конфігурації.
    """
    APP_NAME = "ProductivityVision ML 1.0 Beta"
    GEOMETRY = "1400x900"
    THEME_MODE = "Dark"
    COLOR_THEME = "blue"

    # Іконка
    ICON_PATH = "Data/icon_PV.ico"

    # Назви файлів
    FILE_DATA = "Data/remote_work_productivity.csv"
    FILE_MODEL_MAIN = "Data/best_xgb.pkl"
    FILE_MODEL_REC = "Data/best_xgbT.pkl"

    # Опції для інтерфейсу
    SORT_OPTIONS = ["Productivity_Score", "Years_Experience", "Job_Satisfaction", "Age", "Job_Level"]
    JOB_LEVEL_ORDER = ['Manager', 'Junior', 'Mid-Level', 'Senior', 'Lead', 'Director']

    # Кольорова палітра UI
    COLOR_HIGH = "#4CAF50"
    COLOR_MED = "#FFC107"
    COLOR_LOW = "#F44336"
    COLOR_BG_CARD = "#2b2b2b"

    # Палітра графіків
    BAR_COLOR = "#F6B26B"
    KDE_CMAP = "Oranges"
    KDE_LINE_COLOR = "#C97A1E"
    VIOLIN_PALETTE = ["#FAD4A5", "#F6B26B"]
