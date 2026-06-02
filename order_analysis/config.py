from pathlib import Path

# Корневая директория проекта
BASE_DIR = Path(__file__).parent.absolute()

# Пути к директориям
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"
LOGS_DIR = BASE_DIR / "logs"

# Пути к выходным файлам
REPORT_OUTPUT = REPORTS_DIR / "analysis_results.csv"
LOG_OUTPUT = LOGS_DIR / "processing_errors.log"

# Параметры обработки
STATUS_COLUMN = "status"
TARGET_STATUS = "Delivered"
ENCODING = "utf-8"