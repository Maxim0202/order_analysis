from pathlib import Path
import config
from src.analyzer import OrderAnalyzer

def main():
    # Точка входа программы: создаём анализатор и запускаем обработку всех CSV-файлов.
    print("--- Старт программы ---")
    print(f"Папка для отчетов: {config.REPORTS_DIR}")
    print(f"Файл отчета: {config.REPORT_OUTPUT}")

    # Создаём объект OrderAnalyzer.
    analyzer = OrderAnalyzer()
    # Обрабатываем всю папку data/ и получаем результаты для каждого файла.
    results = analyzer.analyze_directory()
    print(f"Обработано файлов: {len(results)}")

    # Показываем краткий итог по каждому файлу: успешно или с ошибкой.
    for name, ok, info in results:
        status = "OK" if ok else "ERROR"
        print(f"- {name}: {status}")
        
if __name__ == "__main__":
    # Запускаем main() только когда файл выполняется как скрипт.
    main()