import os
import pandas as pd
import joblib
from typing import Optional, List, Dict
from sklearn.preprocessing import LabelEncoder
from config import Config


class ProductivityEngine:
    """
    Головний контролер логіки застосунку.

    Клас відповідає за:
    - Завантаження та збереження моделей машинного навчання.
    - Обробку та підготовку даних (ETL).
    - Генерацію прогнозів продуктивності.
    - Створення автоматичних рекомендацій для покращення показників.
    - Управління базою даних співробітників у пам'яті.
    """

    def __init__(self, app_path: str):
        """
        Ініціалізує шляхи до файлів, словники для декодування значень
        та базу знань для системи рекомендацій.
        """
        self.app_path = app_path
        self.data_path = os.path.join(app_path, Config.FILE_DATA)
        self.model_main_path = os.path.join(app_path, Config.FILE_MODEL_MAIN)
        self.model_rec_path = os.path.join(app_path, Config.FILE_MODEL_REC)

        self.model_main = None
        self.model_rec = None
        self.df_raw: Optional[pd.DataFrame] = None
        self.df_full: Optional[pd.DataFrame] = None
        self.df_encoded: Optional[pd.DataFrame] = None
        self.feature_names: List[str] = []

        self.le_dept = LabelEncoder()
        self.le_ind = LabelEncoder()

        self.decoding_maps = {
            'Education_Level': {0: 'High School', 1: 'Associate Degree', 2: 'Bachelor Degree', 3: 'Professional Degree',
                                4: 'Master Degree', 5: 'PhD'},
            'Marital_Status': {0: 'Single', 1: 'Divorced', 2: 'In Relationship', 3: 'Married'},
            'Job_Level': {0: 'Manager', 1: 'Junior', 2: 'Mid-Level', 3: 'Senior', 4: 'Lead', 5: 'Director'},
            'Gender': {0: 'Male', 1: 'Female', 2: 'Non-binary'},
            'Has_Children': {0: 'No', 1: 'Yes'},
            'Location_Type': {0: 'Rural', 1: 'Suburban', 2: 'Urban'},
            'Company_Size': {'Startup (1-50)': 0, 'Small (51-200)': 1, 'Medium (201-1000)': 2, 'Large (1001-5000)': 3,
                             'Enterprise (5000+)': 4},
            'Home_Office_Quality': {'Poor': 0, 'Average': 1, 'Excellent': 2, 'Good': 3},
            'Internet_Speed_Category': {'Slow (<25 Mbps)': 0, 'Moderate (25-50 Mbps)': 1, 'Fast (50-100 Mbps)': 2,
                                        'Very Fast (100+ Mbps)': 3},
            'Manager_Support_Level': {'Low': 0, 'Moderate': 1, 'High': 2, 'Very Low': 3, 'Very High': 4},
            'Team_Collaboration_Frequency': {'Monthly': 0, 'Bi-weekly': 1, 'Weekly': 2, 'Few times per week': 3,
                                             'Daily': 4},
            'Response_Quality': {'Low': 0, 'Medium': 1, 'High': 2}
        }

        self.advice_map = {
            'Job_Satisfaction': {
                'increase': "Утримання (Retention). Переглянути систему бонусів, карту кар'єрного росту та нематеріальну мотивацію.",
                'decrease': "Перевірка реальності. Можливо, працівник ігнорує проблеми або 'вигорає', приховуючи це за високою оцінкою."
            },
            'Manager_Support_Level': {
                'increase': "Менторство. Менеджеру варто запровадити регулярні 1:1, допомагати з пріоритезацією та давати чіткий фідбек.",
                'decrease': "Автономія. Зменшити рівень мікроменеджменту, надати більше свободи у прийнятті рішень."
            },
            'Stress_Level': {
                'increase': "Челендж (Eustress). Робота занадто монотонна. Додати амбітних цілей або нових проектів для драйву.",
                'decrease': "Well-being. Критичний рівень! Запропонувати відпустку, перерозподілити навантаження, забезпечити консультацію психолога."
            },
            'Home_Office_Quality': {
                'increase': "Апгрейд місця. Виділити бюджет на ергономічне крісло, другий монітор або шумопоглинаючі навушники.",
                'decrease': "Неактуально. Погіршення фізичних умов праці завжди веде до зниження продуктивності."
            },
            'Location_Type': {
                'change': "Зміна обстановки. Розглянути можливість релокації або надання доступу до мережі коворкінгів для різноманіття."
            },
            'Commute_Time_Minutes': {
                'increase': "Не рекомендовано. (Модель може бачити зв'язок з офісною соціалізацією, але краще вирішувати це через тімбілдінги).",
                'decrease': "Економія ресурсу. Дозволити працювати з дому в дні пікового навантаження на дорогах або змістити графік."
            },
            'Internet_Speed_Category': {
                'increase': "Технічне забезпечення. Компенсувати вартість гігабітного інтернету, надати 4G-модем або Starlink як резерв.",
                'decrease': "Перевірка VPN. Якщо швидкість надлишкова, переконайтеся, що корпоративні засоби безпеки не 'ріжуть' канал дарма."
            },
            'WFH_Days_Per_Week': {
                'increase': "Фокус (Deep Work). Працівнику потрібно більше тиші для складних задач. Збільшити кількість днів вдома.",
                'decrease': "Соціалізація. Працівник ізольований. Рекомендується частіше з'являтися в офісі для командної взаємодії."
            },
            'Work_Hours_Per_Week': {
                'increase': "Недозавантаження. Співробітник готовий взяти на себе більше відповідальності або менторити новачків.",
                'decrease': "Ризик вигорання. Суворий контроль овертаймів, делегування рутинних задач, перегляд естімейтів."
            },
            'Work_Life_Balance': {
                'increase': "Кордони. Заборонити робочі чати у вихідні/вечір, стимулювати використання відпусток.",
                'decrease': "Гнучкість (Work-Life Integration). Дозволити розривати робочий день для особистих справ із допрацюванням пізніше."
            },
            'Meetings_Per_Week': {
                'increase': "Синхронізація. Втрата контексту. Додати короткі дейлі-мітинги або регулярні синки з командою.",
                'decrease': "Боротьба з 'Zoom Fatigue'. Ввести 'дні тиші' (без дзвінків), замінити частину мітингів асинхронними звітами."
            },
            'Team_Collaboration_Frequency': {
                'increase': "Синергія. Стимулювати парне програмування, спільні брейншторми та неформальне спілкування.",
                'decrease': "Захист уваги. Мінімізувати відволикання в чатах, впровадити культуру 'асинхронності' за замовчуванням."
            }
        }

    def load_resources(self) -> None:
        """
        Завантажує серіалізовані моделі (.pkl) та файл даних (.csv).
        Виконує початкову підготовку даних, формує повний датасет
        та розраховує продуктивність для наявних записів.
        """
        if not os.path.exists(self.model_main_path):
            raise FileNotFoundError(f"Main Model not found: {self.model_main_path}")
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"Data file not found: {self.data_path}")

        self.model_main = joblib.load(self.model_main_path)
        if os.path.exists(self.model_rec_path):
            self.model_rec = joblib.load(self.model_rec_path)

        self.df_raw = pd.read_csv(self.data_path)

        X = self.df_raw.drop('Employee_ID', axis=1).copy()
        X = self._preprocess_data(X, fit_encoders=True)
        self.df_encoded = X.copy()
        self.feature_names = X.columns.tolist()

        predictions = self.model_main.predict(X)
        self.df_full = self.df_raw.copy()
        self.df_full['Productivity_Score'] = predictions

        if self.df_full['Productivity_Score'].max() <= 1.0:
            self.df_full['Productivity_Score'] *= 100

        self.df_full['Job_Level'] = pd.Categorical(
            self.df_full['Job_Level'], categories=Config.JOB_LEVEL_ORDER, ordered=True
        )

    def _preprocess_data(self, df: pd.DataFrame, fit_encoders=False) -> pd.DataFrame:
        """
        Здійснює попередню обробку даних перед подачею в модель.
        Включає перетворення дат, маппінг категоріальних значень
        у числові коди та кодування через LabelEncoder.
        """
        X = df.copy()
        if 'Survey_Date' in X.columns:
            X['Survey_Date'] = pd.to_datetime(X['Survey_Date'])
            start_date = X['Survey_Date'].min()
            X['Survey_Date'] = (X['Survey_Date'] - start_date).dt.days

        mappings = {
            'Education_Level': {'High School': 0, 'Associate Degree': 1, 'Bachelor Degree': 2, 'Professional Degree': 3,
                                'Master Degree': 4, 'PhD': 5},
            'Marital_Status': {'Single': 0, 'Divorced': 1, 'In Relationship': 2, 'Married': 3},
            'Gender': {'Male': 0, 'Female': 1, 'Non-binary': 2},
            'Has_Children': {'No': 0, 'Yes': 1},
            'Location_Type': {'Rural': 0, 'Suburban': 1, 'Urban': 2},
            'Job_Level': {'Manager': 0, 'Junior': 1, 'Mid-Level': 2, 'Senior': 3, 'Lead': 4, 'Director': 5},
            'Company_Size': {'Startup (1-50)': 0, 'Small (51-200)': 1, 'Medium (201-1000)': 2, 'Large (1001-5000)': 3,
                             'Enterprise (5000+)': 4},
            'Home_Office_Quality': {'Poor': 0, 'Average': 1, 'Excellent': 2, 'Good': 3},
            'Internet_Speed_Category': {'Slow (<25 Mbps)': 0, 'Moderate (25-50 Mbps)': 1, 'Fast (50-100 Mbps)': 2,
                                        'Very Fast (100+ Mbps)': 3},
            'Manager_Support_Level': {'Low': 0, 'Moderate': 1, 'High': 2, 'Very Low': 3, 'Very High': 4},
            'Team_Collaboration_Frequency': {'Monthly': 0, 'Bi-weekly': 1, 'Weekly': 2, 'Few times per week': 3,
                                             'Daily': 4},
            'Response_Quality': {'Low': 0, 'Medium': 1, 'High': 2}
        }
        for col, mapping in mappings.items():
            if col in X.columns: X[col] = X[col].map(mapping)

        if fit_encoders:
            if 'Department' in X.columns: X['Department'] = self.le_dept.fit_transform(X['Department'])
            if 'Industry' in X.columns: X['Industry'] = self.le_ind.fit_transform(X['Industry'])
        else:
            if 'Department' in X.columns: X['Department'] = self.le_dept.transform(X['Department'])
            if 'Industry' in X.columns: X['Industry'] = self.le_ind.transform(X['Industry'])
        return X

    def get_recommendations(self, emp_id: str) -> pd.DataFrame:
        """
        Аналізує дані співробітника та генерує рекомендації.
        Використовує метод 'what-if' аналізу: змінює параметри
        впливу (features) та перевіряє реакцію моделі.
        Повертає DataFrame з переліком дій та прогнозованим приростом продуктивності.
        """
        if self.model_rec is None: return pd.DataFrame()

        emp_row_raw = self.df_raw[self.df_raw['Employee_ID'] == emp_id]
        if emp_row_raw.empty: return pd.DataFrame()

        emp_row_encoded = self._preprocess_data(emp_row_raw.drop('Employee_ID', axis=1), fit_encoders=False)
        drop_cols = ['Productivity_Score', 'Efficiency_Rating', 'Quality_Score', 'Task_Completion_Rate',
                     'Innovation_Score']
        cols_to_drop = [c for c in drop_cols if c in emp_row_encoded.columns]
        emp_data_for_model = emp_row_encoded.drop(columns=cols_to_drop)

        actionable_features = list(self.advice_map.keys())
        current_pred = self.model_rec.predict(emp_data_for_model)[0]
        results = []

        for feature in actionable_features:
            if feature not in emp_data_for_model.columns: continue

            min_val = self.df_encoded[feature].min()
            max_val = self.df_encoded[feature].max()
            current_val = emp_data_for_model[feature].values[0]

            scenarios = {'Min': min_val, 'Max': max_val}
            best_gain = 0
            best_val = current_val

            for _, val in scenarios.items():
                if val == current_val: continue
                sim_data = emp_data_for_model.copy()
                sim_data[feature] = val
                new_pred = self.model_rec.predict(sim_data)[0]

                gain = new_pred - current_pred
                if gain > best_gain:
                    best_gain = gain
                    best_val = val

            if best_gain > 0.01:
                decoded_curr = self._decode_value(feature, current_val)
                decoded_best = self._decode_value(feature, best_val)

                if best_val > current_val:
                    direction = 'increase'
                    if feature in self.decoding_maps:
                        action = f"Підвищити до '{decoded_best}'"
                    else:
                        action = f"Підняти до {decoded_best}"
                else:
                    direction = 'decrease'
                    if feature in self.decoding_maps:
                        action = f"Знизити до '{decoded_best}'"
                    else:
                        action = f"Знизити до {decoded_best}"

                advice_entry = self.advice_map.get(feature, {})
                advice_text = advice_entry.get(direction)

                if not advice_text:
                    advice_text = advice_entry.get('change')
                    action = f"Змінити на '{decoded_best}'"

                if not advice_text:
                    advice_text = "Оптимізувати цей показник для покращення результату."

                results.append({
                    'Ознака': feature,
                    'Поточне': decoded_curr,
                    'Рекомендація': decoded_best,
                    'Дія': action,
                    'Приріст (%)': best_gain,
                    'Порада': advice_text
                })

        if not results: return pd.DataFrame()
        return pd.DataFrame(results).sort_values(by='Приріст (%)', ascending=False)

    def _decode_value(self, feature: str, value: float) -> str:
        """
        Конвертує числове значення категорії назад у зрозумілий текст
        використовуючи decoding_maps.
        """
        if feature in self.decoding_maps:
            return self.decoding_maps[feature].get(int(value), value)
        return value

    def get_data(self, sort_by: str, top_n: int, order_mode: str = "Спадання") -> pd.DataFrame:
        """
        Отримує відфільтровані та відсортовані дані для відображення
        у таблиці (Dashboard).
        """
        if self.df_full is None: return pd.DataFrame()
        sort_col = sort_by if sort_by in self.df_full.columns else "Productivity_Score"
        df_result = self.df_full.copy()

        if order_mode == "Випадково":
            df_result = df_result.sample(frac=1)
        else:
            df_result = df_result.sort_values(by=sort_col, ascending=(order_mode == "Зростання"))
        return df_result.head(top_n)

    def find_employee(self, emp_id: str) -> Optional[pd.Series]:
        """
        Шукає співробітника за унікальним ID в завантаженому датасеті.
        Повертає серію даних або None, якщо не знайдено.
        """
        if self.df_full is None: return None
        result = self.df_full[self.df_full['Employee_ID'] == emp_id]
        return result.iloc[0] if not result.empty else None

    def get_feature_importances(self) -> pd.DataFrame:
        """
        Витягує важливість ознак (feature importance) з основної моделі ML.
        Корисно для аналітики факторів впливу.
        """
        if self.model_main is None or not hasattr(self.model_main, 'feature_importances_'):
            return pd.DataFrame()
        return pd.DataFrame({
            'Feature': self.feature_names, 'Importance': self.model_main.feature_importances_
        }).sort_values(by='Importance', ascending=False).head(12)

    def generate_new_id(self) -> str:
        """
        Генерує новий унікальний ID для співробітника, базуючись на
        останньому існуючому ID в базі (наприклад, EMP010 -> EMP011).
        """
        if self.df_raw is None or self.df_raw.empty:
            return "EMP001"

        ids = self.df_raw['Employee_ID'].astype(str).str.extract(r'(\d+)').astype(int)
        max_id = ids.max().item() if not ids.empty else 0
        new_id = max_id + 1
        return f"EMP{new_id:04d}"

    def add_new_employee(self, data_dict: dict) -> str:
        """
        Додає нового співробітника в систему.

        Процес включає:
        1. Генерацію ID та поточної дати.
        2. Прогнозування продуктивності за допомогою моделі.
        3. Оновлення внутрішніх DataFrame.
        4. Повернення нового ID.
        """
        new_id = self.generate_new_id()
        current_date = pd.Timestamp.now().strftime("%Y-%m-%d")

        row = data_dict.copy()
        row['Employee_ID'] = new_id
        row['Survey_Date'] = current_date

        new_df = pd.DataFrame([row])

        try:
            X = self._preprocess_data(new_df, fit_encoders=False)

            model_cols = self.model_main.feature_names_in_
            X_ready = X.reindex(columns=model_cols, fill_value=0)

            pred_score = self.model_main.predict(X_ready)[0]

            if pred_score <= 1.0: pred_score *= 100

            row['Productivity_Score'] = pred_score

            for missing in ['Efficiency_Rating', 'Quality_Score', 'Task_Completion_Rate', 'Innovation_Score']:
                if missing not in row:
                    row[missing] = 0.0

        except Exception as e:
            print(f"ML Error during add: {e}")
            row['Productivity_Score'] = 0.0

        final_row_df = pd.DataFrame([row])

        self.df_raw = pd.concat([self.df_raw, final_row_df], ignore_index=True)
        self.df_full = pd.concat([self.df_full, final_row_df], ignore_index=True)

        self.df_full['Job_Level'] = pd.Categorical(
            self.df_full['Job_Level'], categories=Config.JOB_LEVEL_ORDER, ordered=True
        )

        # ОПЦІОНАЛЬНО: Зберегти у CSV
        # self.df_raw.to_csv(self.data_path, index=False)

        return new_id
