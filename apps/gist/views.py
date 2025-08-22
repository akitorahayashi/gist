import logging

from celery.result import AsyncResult
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from .services import ScrapingService
from .tasks import process_url_task

logger = logging.getLogger(__name__)


@require_GET
def index(request):
    """初期ページを表示します。"""
    return render(request, "gist/index.html")


@require_POST
def start_task(request):
    """URLを受け取り、非同期処理タスクを開始します。"""
    url = request.POST.get("url")
    if not url:
        return JsonResponse({"error": "URLを入力してください。"}, status=400)

    try:
        # URLの形式だけを素早く検証
        ScrapingService.validate_url(url)
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)

    # Celeryタスクを開始
    task = process_url_task.delay(url)
    return JsonResponse({"task_id": task.id}, status=202)


@require_GET
def get_status(request, task_id):
    """タスクIDを受け取り、現在のステータスや結果を返します。"""
    task_result = AsyncResult(task_id)

    # タスクがバックエンドに存在しないかチェック
    # get_task_metaはタスクが存在しない場合Noneを返す
    if not task_result.backend.get_task_meta(task_id):
        return JsonResponse({"status": "error", "message": "タスクが見つかりません。"}, status=404)

    if task_result.state == "PENDING":
        response = {"status": "processing", "message": "タスクは待機中です。"}
    elif task_result.state in ("PROGRESS", "STARTED"):
        response = {
            "status": "processing",
            "message": (task_result.info or {}).get("message", "処理中..."),
        }
    elif task_result.state == "SUCCESS":
        result = task_result.result
        response = {
            "status": "success",
            "title": result.get("title"),
            "summary": result.get("summary"),
        }
    elif task_result.state == "FAILURE":
        # エラーメッセージを取得
        # task_result.result にはExceptionオブジェクトが入っている
        error_message = str(task_result.result)
        response = {"status": "error", "message": error_message}
    else:
        # その他の状態（REVOKEDなど）
        response = {"status": "unknown", "message": f"不明なステータス: {task_result.state}"}

    return JsonResponse(response)
