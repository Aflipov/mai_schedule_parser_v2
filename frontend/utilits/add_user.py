# utils/add_user.py
import requests

API_URL = "http://localhost:8000/users/"

def add_user():
    username = input("Enter username: ")
    email = input("Enter email: ")
    password = input("Enter password: ")

    user_data = {
        "username": username,
        "email": email,
        "password": password
    }

    try:
        response = requests.post(API_URL, json=user_data)
        response.raise_for_status()
        print("User created successfully!")
    except requests.exceptions.RequestException as e:
        print(f"Failed to create user: {e}")

if __name__ == "__main__":
    add_user()