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
        Test getting the status of a non-existent task.
        """
        task_id = str(uuid.uuid4())
        # state が存在しないタスクIDを模倣するために、stateをNoneに設定
        mock_result = mock_async_result.return_value
        mock_result.state = None

        url = reverse("gist:get_status", kwargs={"task_id": task_id})
        response = self.client.get(url)

        # 存在しないタスクIDの場合、CeleryはPENDINGを返すことがあるため、
        # ここではstateが返ってこないか、特定の状態でないことを確認する。
        # 今回はシンプルに404を期待する。
        # 注: 実際のAPI実装で、存在しないタスクIDに対して404を返すようにする必要がある。
        # AsyncResultはタスクが存在しなくても例外を投げないため、
        # stateをチェックしてハンドリングする。
        # ここでは、ビューがNoneのstateを404にマッピングすると仮定する。
        # テストをより堅牢にするため、ビューの実装に合わせて調整が必要。
        #
        # 更新: ビュー側で state がない (AsyncResultが情報を返さない) 場合を
        # 404 Not Found として扱うように実装するため、テストもそれに合わせる。
        # モックを調整して、stateが存在しない状態をシミュレートする。
        mock_result.state = "PENDING"  # Celeryのデフォルトの振る舞い
        mock_result.info = None  # 結果も情報もない

        # 実際のビューでは、task_id がDBや結果バックエンドに存在しない場合を
        # 判定する必要がある。ここではAsyncResultの振る舞いを模倣する。
        # 簡単のため、stateが特定の状態でない場合に404を返すロジックをビューに期待する。
        # ここでは、mock_result.get()が例外を出すケースなどをシミュレートできるが、
        # 今回は state をもとにビューが判断すると仮定する。
        #
        # 最終的なアプローチ：ビュー側で`result.backend.get_task_meta(task_id)`を使って
        # タスクのメタデータが存在するかを確認する方法が確実。
        # テストでは、そのメソッドがNoneを返すようにパッチする。
        with patch.object(
            mock_async_result.return_value.backend, "get_task_meta", return_value=None
        ) as mock_get_meta:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 404)
            mock_get_meta.assert_called_once_with(task_id)
