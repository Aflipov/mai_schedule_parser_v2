# frontend/main.py
import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout,
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QMessageBox)
import requests
import logging

# Настройка логирования
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

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
        logging.debug(f"Attempting to login with username: {username}")

        try:
            response = requests.post(TOKEN_URL, data={"username": username, "password": password}, timeout=10)  # Добавлено время ожидания
            response.raise_for_status()  # Проверка статуса HTTP
            response_json = response.json()
            self.token = response_json.get("access_token")
            if self.token:
                QMessageBox.information(self, "Success", "Login successful!")
                logging.info("Login successful!")
            else:
                QMessageBox.warning(self, "Warning", "Login successful, but no token received.")
                logging.warning("Login successful, but no token received. Response: %s", response_json)
        except requests.exceptions.Timeout as e:
            self.display_error_message(f"Login failed: Timeout error. Check server and network. {e}")
            logging.error(f"Login failed: Timeout error. Check server and network. {e}")
        except requests.exceptions.ConnectionError as e:
            self.display_error_message(f"Login failed: Connection error. Check server availability. {e}")
            logging.error(f"Login failed: Connection error. Check server availability. {e}")
        except requests.exceptions.HTTPError as e:
            self.display_error_message(f"Login failed: HTTP error {e.response.status_code}. Check credentials. {e}")
            logging.error(f"Login failed: HTTP error. Status code: {e.response.status_code}.  {e.response.text if hasattr(e.response, 'text') else ''} {e}")
        except ValueError as e:
            self.display_error_message(f"Login failed: Invalid JSON response. Check server response. {e}")
            logging.error(f"Login failed: Invalid JSON response.  {e} Response text: {response.text if 'response' in locals() and hasattr(response, 'text') else 'No response'}")
        except Exception as e:
            self.display_error_message(f"Login failed: An unexpected error occurred. {e}")
            logging.exception(f"Login failed: An unexpected error occurred. {e}")


    def fetch_schedule(self):
        """Получает расписание с сервера и отображает его."""
        group_number = self.group_input.text()
        if not group_number:
            self.display_error_message("Please enter a group number.")
            return

        if not self.token:
            self.display_error_message("Please login first.")
            return

        headers = {"Authorization": f"Bearer {self.token}"}
        try:
            response = requests.get(SCHEDULE_URL, headers=headers, params={"group_numbers": [group_number]}, timeout=10) # добавлено время ожидания
            response.raise_for_status()
            schedule_data = response.json()
            if isinstance(schedule_data, list):
                self.display_schedule(schedule_data)
            else:
                self.display_error_message("Invalid data received from server.")
        except requests.exceptions.Timeout as e:
            self.display_error_message(f"Fetch schedule failed: Timeout error. Check server and network. {e}")
            logging.error(f"Fetch schedule failed: Timeout error. Check server and network. {e}")
        except requests.exceptions.ConnectionError as e:
            self.display_error_message(f"Fetch schedule failed: Connection error. Check server availability. {e}")
            logging.error(f"Fetch schedule failed: Connection error. Check server availability. {e}")
        except requests.exceptions.HTTPError as e:
            self.display_error_message(f"Fetch schedule failed: HTTP error {e.response.status_code}. Check token and permissions. {e}")
            logging.error(f"Fetch schedule failed: HTTP error. Status code: {e.response.status_code}.  {e.response.text if hasattr(e.response, 'text') else ''} {e}")
        except ValueError as e:
            self.display_error_message(f"Fetch schedule failed: Invalid JSON response. Check server response. {e}")
            logging.error(f"Fetch schedule failed: Invalid JSON response.  {e} Response text: {response.text if 'response' in locals() and hasattr(response, 'text') else 'No response'}")
        except Exception as e:
            self.display_error_message(f"Fetch schedule failed: An unexpected error occurred. {e}")
            logging.exception(f"Fetch schedule failed: An unexpected error occurred. {e}")


    def display_schedule(self, schedule_data):
        """Отображает расписание в QTableWidget."""
        if not schedule_data:
            self.display_error_message("No schedule data found.")
            return

        self.schedule_table.setRowCount(len(schedule_data))
        self.schedule_table.setColumnCount(4)
        self.schedule_table.setHorizontalHeaderLabels(["Subject", "Teacher", "Time", "Classroom"])

        for row, lesson in enumerate(schedule_data):
            try:
                self.schedule_table.setItem(row, 0, QTableWidgetItem(lesson["subject"]["name"]))
                self.schedule_table.setItem(row, 1, QTableWidgetItem(lesson["teacher"]["name"]))
                self.schedule_table.setItem(row, 2, QTableWidgetItem(lesson["start_time"]))
                self.schedule_table.setItem(row, 3, QTableWidgetItem(lesson["classroom"]["name"]))
            except (KeyError, TypeError) as e:
                logging.error(f"Error displaying schedule data: {e} - lesson: {lesson}")
                self.display_error_message("Error displaying schedule data. Check server response.")

    def display_error_message(self, message):
        """Отображает сообщение об ошибке в интерфейсе."""
        QMessageBox.critical(self, "Error", message)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    schedule_app = ScheduleApp()
    schedule_app.show()
    sys.exit(app.exec_())