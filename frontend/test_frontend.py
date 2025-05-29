# frontend/test_frontend.py
import unittest
from unittest.mock import patch, MagicMock  # Import patch and MagicMock
import requests  # Import requests (для мокирования HTTP запросов)
from frontend import main2  # Import your GUI application code

class TestFrontend(unittest.TestCase):

    @patch('requests.get')  # Mock requests.get
    def test_get_schedule_success(self, mock_get):
        """Test successful retrieval of schedule data from server."""

        # Configure mock to return a successful response with sample data
        mock_get.return_value = MagicMock(status_code=200)
        mock_get.return_value.json.return_value = [
            {"id": 1, "subject": "Math", "teacher": "Mr. Smith", "start_time": "2024-01-30T10:00:00"}
        ]

        # Run your GUI code to fetch and display the schedule (replace with your actual function)
        schedule_data = main2.get_schedule_from_server()

        # Assert that the server returned data
        self.assertEqual(len(schedule_data), 1)
        self.assertEqual(schedule_data[0]["subject"], "Math")

    @patch('requests.get')  # Mock requests.get
    def test_get_schedule_failure(self, mock_get):
        """Test handling of server errors when retrieving schedule data."""

        # Configure mock to return an error status code
        mock_get.return_value = MagicMock(status_code=500)

        # Run your GUI code to fetch and display the schedule
        schedule_data = main2.get_schedule_from_server()  # Replace with your function

        # Assert that the GUI handles the error correctly (e.g., displays an error message)
        self.assertEqual(len(schedule_data), 0)  # Assuming your function returns an empty list on error
        # You might want to assert that the error message in GUI updates

    @patch('requests.post')  # Mock requests.post
    def test_submit_new_schedule(self, mock_post):
        """Test successful submission of new schedule data to server."""

        # Configure mock to return a successful response
        mock_post.return_value = MagicMock(status_code=201) # Successful creation
        mock_post.return_value.json.return_value = {"id": 2, "subject": "Physics"} # Sample data

        # Run your GUI code to submit new schedule data to server
        new_schedule = {"subject": "Physics", "teacher": "Ms. Johnson"}
        response = main2.submit_schedule_to_server(new_schedule)  # Replace with your submit function

        # Assert the new data is successfuly send
        self.assertEqual(response["subject"], "Physics")

if __name__ == '__main__':
    unittest.main()