import json
import uuid
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse


class GistApiTests(TestCase):
    @patch("apps.gist.views.process_url_task.delay")
    def test_start_task_valid_url(self, mock_delay):
        """
        Test that a valid URL returns 202 and a task_id.
        """
        # モックされた delay メソッドが返すオブジェクトに id 属性を設定
        mock_task = mock_delay.return_value
        mock_task.id = str(uuid.uuid4())

        url = reverse("gist:start_task")
        response = self.client.post(url, {"url": "http://example.com"})

        self.assertEqual(response.status_code, 202)
        self.assertIn("task_id", response.json())
        self.assertEqual(response.json()["task_id"], mock_task.id)
        mock_delay.assert_called_once_with("http://example.com")

    def test_start_task_invalid_url(self):
        """
        Test that an invalid URL returns a 400 bad request.
        """
        url = reverse("gist:start_task")
        response = self.client.post(url, {"url": "not-a-valid-url"})

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())

    def test_start_task_missing_url(self):
        """
        Test that a missing URL returns a 400 bad request.
        """
        url = reverse("gist:start_task")
        response = self.client.post(url, {})

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())

    @patch("apps.gist.views.AsyncResult")
    def test_get_status_pending(self, mock_async_result):
        """
        Test getting the status of a pending task.
        """
        task_id = str(uuid.uuid4())
        mock_result = mock_async_result.return_value
        mock_result.state = "PENDING"
        mock_result.info = None

        url = reverse("gist:get_status", kwargs={"task_id": task_id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "processing")
        self.assertEqual(data["message"], "タスクは待機中です。")

    @patch("apps.gist.views.AsyncResult")
    def test_get_status_processing(self, mock_async_result):
        """
        Test getting the status of a processing task with a custom message.
        """
        task_id = str(uuid.uuid4())
        mock_result = mock_async_result.return_value
        mock_result.state = "PROGRESS"
        mock_result.info = {"message": "スクレイピング中..."}

        url = reverse("gist:get_status", kwargs={"task_id": task_id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "processing")
        self.assertEqual(data["message"], "スクレイピング中...")

    @patch("apps.gist.views.AsyncResult")
    def test_get_status_success(self, mock_async_result):
        """
        Test getting the status of a successful task.
        """
        task_id = str(uuid.uuid4())
        mock_result = mock_async_result.return_value
        mock_result.state = "SUCCESS"
        mock_result.result = {
            "title": "Example Domain",
            "summary": "This is a summary.",
        }

        url = reverse("gist:get_status", kwargs={"task_id": task_id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["title"], "Example Domain")
        self.assertEqual(data["summary"], "This is a summary.")

    @patch("apps.gist.views.AsyncResult")
    def test_get_status_failure(self, mock_async_result):
        """
        Test getting the status of a failed task.
        """
        task_id = str(uuid.uuid4())
        mock_result = mock_async_result.return_value
        mock_result.state = "FAILURE"
        mock_result.result = "An error occurred."

        url = reverse("gist:get_status", kwargs={"task_id": task_id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "error")
        self.assertEqual(data["message"], "An error occurred.")

    @patch("apps.gist.views.AsyncResult")
    def test_get_status_not_found(self, mock_async_result):
        """
        Test getting the status of a non-existent task returns a pending status.
        """
        task_id = str(uuid.uuid4())
        mock_result = mock_async_result.return_value
        # Celery's default behavior for an unknown task is to return a PENDING state.
        mock_result.state = "PENDING"
        mock_result.info = None

        url = reverse("gist:get_status", kwargs={"task_id": task_id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "processing")
        self.assertEqual(data["message"], "タスクは待機中です。")

    @patch("apps.gist.views.AsyncResult")
    def test_get_status_started(self, mock_async_result):
        """
        Test getting the status of a started task.
        """
        task_id = str(uuid.uuid4())
        mock_result = mock_async_result.return_value
        mock_result.state = "STARTED"
        mock_result.info = None

        url = reverse("gist:get_status", kwargs={"task_id": task_id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "processing")
        self.assertEqual(data["message"], "処理中...")

    def test_start_task_get_method_not_allowed(self):
        """
        Test that GET request to start_task returns 405.
        """
        url = reverse("gist:start_task")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)

    def test_get_status_post_method_not_allowed(self):
        """
        Test that POST request to get_status returns 405.
        """
        task_id = str(uuid.uuid4())
        url = reverse("gist:get_status", kwargs={"task_id": task_id})
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 405)

    @patch("apps.gist.views.process_url_task.delay")
    def test_start_task_valid_url_json(self, mock_delay):
        """
        Test that a valid URL sent as JSON returns 202.
        """
        mock_task = mock_delay.return_value
        mock_task.id = str(uuid.uuid4())
        url = reverse("gist:start_task")
        response = self.client.post(
            url,
            data=json.dumps({"url": "https://example.com"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.json()["task_id"], mock_task.id)
        mock_delay.assert_called_once_with("https://example.com")

    @patch("apps.gist.views.process_url_task.delay")
    def test_start_task_broker_down_returns_503(self, mock_delay):
        """
        Test that a 503 is returned if the task broker is down.
        """
        mock_delay.side_effect = RuntimeError("broker down")
        url = reverse("gist:start_task")
        response = self.client.post(url, {"url": "https://example.com"})
        self.assertEqual(response.status_code, 503)
        self.assertIn("error", response.json())

    @patch("apps.gist.views.AsyncResult")
    def test_get_status_retry(self, mock_async_result):
        """
        Test getting the status of a retrying task.
        """
        task_id = str(uuid.uuid4())
        mock_result = mock_async_result.return_value
        mock_result.state = "RETRY"
        mock_result.info = None
        url = reverse("gist:get_status", kwargs={"task_id": task_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "processing")
        self.assertIn("再試行中", data["message"])

    @patch("apps.gist.views.AsyncResult")
    def test_get_status_revoked(self, mock_async_result):
        """
        Test getting the status of a revoked task.
        """
        task_id = str(uuid.uuid4())
        mock_result = mock_async_result.return_value
        mock_result.state = "REVOKED"
        mock_result.info = None
        url = reverse("gist:get_status", kwargs={"task_id": task_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "error")
        self.assertIn("取り消されました", data["message"])
