# frontend/main.py
import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout,
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QMessageBox)
import requests

# URL вашего FastAPI сервера
API_URL = "http://localhost:8000"
TOKEN_URL = f"{API_URL}/users/token"
SCHEDULE_URL = f"{API_URL}/schedule/"

class ScheduleApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Schedule Viewer")
        self.setGeometry(100, 100, 800, 600)  # x, y, width, height

        # Элементы интерфейса
        self.username_input = QLineEdit(self)
        self.password_input = QLineEdit(self)
        self.password_input.setEchoMode(QLineEdit.Password)
        self.login_button = QPushButton("Login", self)
        self.group_input = QLineEdit(self)
        self.fetch_button = QPushButton("Fetch Schedule", self)
        self.schedule_table = QTableWidget(self)

        # Обработчики нажатия кнопок
        self.login_button.clicked.connect(self.login)
        self.fetch_button.clicked.connect(self.fetch_schedule)

        # Разметка
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Username:"))
        layout.addWidget(self.username_input)
        layout.addWidget(QLabel("Password:"))
        layout.addWidget(self.password_input)
        layout.addWidget(self.login_button)
        layout.addWidget(QLabel("Group Number:"))
        layout.addWidget(self.group_input)
        layout.addWidget(self.fetch_button)
        layout.addWidget(self.schedule_table)
        self.setLayout(layout)

        self.token = None

    def login(self):
        """Получает JWT токен для аутентификации."""
        username = self.username_input.text()
        password = self.password_input.text()
        try:
            response = requests.post(TOKEN_URL, data={"username": username, "password": password})
            response.raise_for_status()
            self.token = response.json().get("access_token")
            QMessageBox.information(self, "Success", "Login successful!")
        except requests.exceptions.RequestException as e:
            self.display_error_message(f"Login failed: {e}")
            print(f"Login failed: {e}")

    def fetch_schedule(self):
        """Получает расписание с сервера и отображает его."""
        group_number = self.group_input.text()
        if not group_number:
            self.display_error_message("Please enter a group number.")
            return

        headers = {"Authorization": f"Bearer {self.token}"}
        try:
            response = requests.get(SCHEDULE_URL, headers=headers, params={"group_numbers": [group_number]})
            response.raise_for_status()
            schedule_data = response.json()
            if isinstance(schedule_data, list):
                self.display_schedule(schedule_data)
            else:
                self.display_error_message("Invalid data received from server.")
        except requests.exceptions.RequestException as e:
            self.display_error_message(f"Network error: {e}")
        except ValueError as e:
            self.display_error_message(f"Error decoding JSON: {e}")

    def display_schedule(self, schedule_data):
        """Отображает расписание в QTableWidget."""
        if not schedule_data:
            self.display_error_message("No schedule data found.")
            return

        self.schedule_table.setRowCount(len(schedule_data))
        self.schedule_table.setColumnCount(4)
        self.schedule_table.setHorizontalHeaderLabels(["Subject", "Teacher", "Time", "Classroom"])

        for row, lesson in enumerate(schedule_data):
            self.schedule_table.setItem(row, 0, QTableWidgetItem(lesson["subject"]["name"]))
            self.schedule_table.setItem(row, 1, QTableWidgetItem(lesson["teacher"]["name"]))
            self.schedule_table.setItem(row, 2, QTableWidgetItem(lesson["start_time"]))
            self.schedule_table.setItem(row, 3, QTableWidgetItem(lesson["classroom"]["name"]))

    def display_error_message(self, message):
        """Отображает сообщение об ошибке в интерфейсе."""
        QMessageBox.critical(self, "Error", message)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    schedule_app = ScheduleApp()
    schedule_app.show()
    sys.exit(app.exec_())