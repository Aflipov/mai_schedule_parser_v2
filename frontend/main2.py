# frontend/main.py
import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout,
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QMessageBox) # Import QMessageBox
import requests

# URL вашего FastAPI сервера
API_URL = "http://localhost:8000/schedule/"  # Замените на фактический URL

class ScheduleApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Schedule Viewer")
        self.setGeometry(100, 100, 800, 600)  # x, y, width, height

        # Элементы интерфейса
        self.group_input = QLineEdit(self)
        self.fetch_button = QPushButton("Fetch Schedule", self)
        self.schedule_table = QTableWidget(self)

        # Обработчик нажатия кнопки
        self.fetch_button.clicked.connect(self.fetch_schedule)

        # Разметка
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Group Number:"))
        layout.addWidget(self.group_input)
        layout.addWidget(self.fetch_button)
        layout.addWidget(self.schedule_table)
        self.setLayout(layout)

    def fetch_schedule(self):
        """Получает расписание с сервера и отображает его."""
        group_number = self.group_input.text()
        if not group_number:
            self.display_error_message("Please enter a group number.")
            return

        try:
            response = requests.get(API_URL, params={"group_numbers": [group_number]})  # Используем "group_numbers" и делаем список
            response.raise_for_status()  # Проверяем статус код
            schedule_data = response.json()  # Получаем JSON данные
            if isinstance(schedule_data, list): # Check if response is a list
                self.display_schedule(schedule_data)  # Отображаем данные в таблице
            else:
                self.display_error_message("Invalid data received from server.")
        except requests.exceptions.RequestException as e:
            # Обработка ошибок сети
            self.display_error_message(f"Network error: {e}")
        except ValueError as e:
            self.display_error_message(f"Error decoding JSON: {e}")

    def display_schedule(self, schedule_data):
        """Отображает расписание в QTableWidget."""
        if not schedule_data:
            self.display_error_message("No schedule data found.")
            return

        self.schedule_table.setRowCount(len(schedule_data))  # Количество строк
        self.schedule_table.setColumnCount(4)  # Количество столбцов
        self.schedule_table.setHorizontalHeaderLabels(["Subject", "Teacher", "Time", "Classroom"])  # Заголовки

        for row, lesson in enumerate(schedule_data):
            self.schedule_table.setItem(row, 0, QTableWidgetItem(lesson["subject"]))  # Предмет
            self.schedule_table.setItem(row, 1, QTableWidgetItem(lesson["teacher"]))  # Преподаватель
            self.schedule_table.setItem(row, 2, QTableWidgetItem(lesson["start_time"]))  # Время
            self.schedule_table.setItem(row, 3, QTableWidgetItem(lesson["classroom"]))  # Аудитория

    def display_error_message(self, message):
        """Отображает сообщение об ошибке в интерфейсе."""
        # Здесь можно добавить QLabel для отображения сообщений об ошибках
        QMessageBox.critical(self, "Error", message) # Use QMessageBox for displaying the error message

if __name__ == "__main__":
    app = QApplication(sys.argv)
    schedule_app = ScheduleApp()
    schedule_app.show()
    sys.exit(app.exec_())