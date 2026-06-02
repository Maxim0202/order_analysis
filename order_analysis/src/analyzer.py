import logging
from pathlib import Path

import config
import pandas as pd

# Класс для анализа заказов: загружает файлы, отбирает доставленные заказы,
# считает метрики и сохраняет результаты в отчет.
class OrderAnalyzer:
    """Класс для анализа данных о заказах интернет-магазина.
    """
    def __init__(self, target_status: str = config.TARGET_STATUS, encoding: str = config.ENCODING):
        """
        Инициализация анализатора.

        Args:
            target_status: Фильтруемый статус заказа (по умолчанию 'Delivered')
            encoding: Кодировка файлов CSV (по умолчанию 'utf-8')
        """
        # Сохраняем настройки в объекте, чтобы использовать их в других методах.
        self.target_status = target_status
        self.encoding = encoding

        # Логгер модуля. Пока он пишет в стандартный логгер Python.
        # Если подключить FileHandler, он будет писать в файл.
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        if not self.logger.handlers:
            config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
            handler = logging.FileHandler(config.LOG_OUTPUT, encoding=self.encoding)
            handler.setFormatter(
                logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
            )
            self.logger.addHandler(handler)

    def load_file(self, file_path: Path) -> pd.DataFrame:
        # Пытаемся загрузить CSV и сразу обработать распространённые ошибки.
        self.error_message = None

        # Если файла нет, сразу возвращаем None и логируем проблему.
        if not file_path.exists():
            self.error_message = f"Файл не найден: {file_path}"
            self.logger.error(self.error_message)
            return None

        try:
            # Читаем файл в pandas.
            df = pd.read_csv(file_path, encoding=self.encoding, sep=',', low_memory=False)

            # Если таблица пуста, считаем это проблемой.
            if df.empty:
                self.error_message = "CSV-файл пуст"
                self.logger.error(self.error_message)
                return None

            self.logger.info(f"Data loaded successfully from {file_path}")
            return df

        except UnicodeDecodeError:
            # Кодировка не соответствует ожидаемой
            self.error_message = f"Ошибка: Файл имеет кодировку, отличную от {self.encoding}"
            self.logger.error(self.error_message)
            return None
        except FileNotFoundError:
            # Низкоуровневая ошибка чтения — файл неожиданно недоступен
            self.error_message = f"Файл {file_path.name} не найден"
            self.logger.error(self.error_message)
            return None
        except Exception as e:
            # Поймаем все остальные ошибки и запишем, что пошло не так
            self.error_message = f"Ошибка при обработке {file_path.name}: {e}"
            self.logger.error(self.error_message)
            return None
        
        
    def filter_delivered_orders(self, df: pd.DataFrame) -> pd.DataFrame:
        # Отбираем только те строки, где статус совпадает с нужным.
        # Здесь важна колонка config.STATUS_COLUMN.
        try:
            filtered_df = df[df[config.STATUS_COLUMN] == self.target_status]
            # Записываем сколько строк получилось после фильтрации.
            self.logger.info(f"Отфильтровано заказов со статусом '{self.target_status}': {len(filtered_df)}")
            return filtered_df
        except KeyError:
            # Если колонки со статусом нет в данных — это пользовательская ошибка данных
            self.error_message = f"Ошибка: Столбец '{config.STATUS_COLUMN}' не найден в таблице."
            self.logger.error(self.error_message)
            return None
        except Exception as e:
            # Любая другая ошибка — логируем и возвращаем None
            self.error_message = f"Ошибка при фильтрации: {e}"
            self.logger.error(self.error_message)
            return None
        

    def calculate_metrics(self, df: pd.DataFrame) -> dict:
        # Считаем метрики по отфильтрованным заказам:
        # количество заказов, выручку и средний чек.
        metrics = {
            'total_orders': 0,
            'total_revenue': None,
            'avg_order_value': None
        }

        # Если данных нет, ничего считать не нужно.
        if df is None or df.empty:
            self.error_message = 'Нет данных для расчёта метрик.'
            self.logger.error(self.error_message)
            return metrics

        # Количество заказов — это просто число строк.
        metrics['total_orders'] = len(df)

        # Суммируем и усредняем колонку total_amount, если она есть.
        if 'total_amount' in df.columns:
            # Приводим к float, чтобы в выходном словаре были стандартные типы
            metrics['total_revenue'] = float(df['total_amount'].sum())
            metrics['avg_order_value'] = float(df['total_amount'].mean())
        else:
            # Если этой колонки нет, просто предупреждаем и возвращаем то, что есть.
            self.logger.warning("Колонка 'total_amount' не найдена, расчёт метрик невозможен.")

        self.logger.info(f"Метрики рассчитаны: {metrics}")
        return metrics
    

    def analyze_file(self, file_path: Path) -> tuple[bool, dict]:
        # Обрабатываем один файл целиком:
        # загрузка, фильтрация, расчёт метрик и запись результата.
        self.error_message = None

        # На вход может прийти строка или Path. Приводим к Path, чтобы было однообразно.
        file_path = Path(file_path)

        try:
            # Шаг 1: загрузка
            file_data = self.load_file(file_path)

            if file_data is None:
                # Ошибка уже сохранена в self.error_message внутри load_file
                self.error_message = f"Файл {file_path} загружен некорректно"
                self.logger.error(self.error_message)
                return False, {"error": self.error_message}

            # Отбираем только доставленные заказы.
            filtered_data = self.filter_delivered_orders(file_data)
            if filtered_data is None:
                # Сообщение об ошибке выставляется в filter_delivered_orders
                msg = self.error_message or f"Ошибка при фильтрации файла {file_path.name}"
                self.logger.error(msg)
                return False, {"error": msg}

            # Теперь считаем нужные метрики.
            metrics = self.calculate_metrics(filtered_data)

            # Собираем результат для одного файла.
            result_row = {
                "file": file_path.name,
                "total_orders": metrics.get("total_orders"),
                "total_revenue": metrics.get("total_revenue"),
                "avg_order_value": metrics.get("avg_order_value"),
            }

            # Пишем результат в общий CSV-отчёт.
            # Первый раз добавляется заголовок.
            config.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
            write_header = not config.REPORT_OUTPUT.exists()
            pd.DataFrame([result_row]).to_csv(
                config.REPORT_OUTPUT, index=False, mode="a", header=write_header, encoding=self.encoding
            )

            # Логируем, что файл обработан.
            self.logger.info(f"Файл {file_path.name} обработан, результаты сохранены в {config.REPORT_OUTPUT}")
            return True, result_row

        except Exception as e:
            # Если что-то пошло не так, пишем в лог и возвращаем ошибка
            # Обрезаем сообщение об ошибке, чтобы оно не было слишком длинным в логе
            error_str = str(e)[:150]  # Берём первые 150 символов ошибки
            self.error_message = f"Неожиданная ошибка при обработке {file_path.name}: {error_str}"
            self.logger.error(self.error_message)
            return False, {"error": self.error_message}
        

    def analyze_directory(self, dir_path: Path = None) -> list[tuple[str, bool, dict]]:
        # Обрабатывает сразу всю папку с CSV-файлами.
        # Если путь не передан, берём папку из config.DATA_DIR.
        if dir_path is None:
            dir_path = config.DATA_DIR

        # Приводим вход к Path, чтобы дальше работать одинаково.
        dir_path = Path(dir_path)
        results = []

        # Если папка не найдена или это не директория, возвращаем пустой список.
        if not dir_path.exists() or not dir_path.is_dir():
            message = f"Папка не найдена или не является директорией: {dir_path}"
            self.logger.error(message)
            return results

        # Собираем все CSV-файлы из папки.
        csv_files = sorted(dir_path.glob("*.csv"))
        if not csv_files:
            self.logger.warning(f"В папке {dir_path} нет CSV-файлов для обработки.")
            return results

        # Обрабатываем каждый файл одним и тем же методом analyze_file.
        for csv_file in csv_files:
            success, result = self.analyze_file(csv_file)
            results.append((csv_file.name, success, result))

        self.logger.info(f"Обработка папки {dir_path} завершена. Файлов: {len(results)}")
        return results