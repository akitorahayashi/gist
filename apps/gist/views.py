import json
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
    if (request.content_type or "").startswith("application/json"):
        try:
            data = json.loads(request.body)
            url = data.get("url")
        except json.JSONDecodeError:
            return JsonResponse({"error": "無効なJSONです。"}, status=400)
    else:
        url = request.POST.get("url")

    # 前後空白を除去（コピー＆ペースト由来のスペース混入対策）
    url = (url or "").strip()
    if not url:
        return JsonResponse({"error": "URLを入力してください。"}, status=400)

    try:
        # URLの形式だけを素早く検証
        ScrapingService.validate_url(url)
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)

    # Celeryタスクを開始
    try:
        task = process_url_task.delay(url)
    except Exception as e:
        logger.exception("Failed to enqueue task for url=%r: %s", url, e)
        return JsonResponse(
            {"error": "タスクをキューに登録できませんでした。しばらくしてから再試行してください。"},
            status=503,
        )
    return JsonResponse({"task_id": task.id}, status=202)


@require_GET
def get_status(request, task_id):
    """タスクIDを受け取り、現在のステータスや結果を返します。"""
    task_result = AsyncResult(task_id)

    # 存在しないタスクIDの場合、Celeryは 'PENDING' を返すことがある。
    # ここでは404を返さず、一貫して「処理中」として扱うことで、
    # フロントエンドのロジックを簡素化し、バックエンドの実装への依存を減らす。
    if task_result.state == "PENDING":
        response = {"status": "processing", "message": "タスクは待機中です。"}
    elif task_result.state in ("PROGRESS", "STARTED"):
        response = {
            "status": "processing",
            "message": (task_result.info or {}).get("message", "処理中..."),
        }
    elif task_result.state == "SUCCESS":
        result = task_result.result
        if isinstance(result, dict):
            response = {
                "status": "success",
                "title": result.get("title"),
                "summary": result.get("summary"),
            }
        else:
            response = {
                "status": "success",
                "title": "要約結果",
                "summary": "" if result is None else str(result),
            }
    elif task_result.state == "FAILURE":
        info = getattr(task_result, "info", None)
        if isinstance(info, dict) and info.get("message"):
            error_message = info["message"]
        else:
            error_message = str(task_result.result)
        response = {"status": "error", "message": error_message}
    elif task_result.state in ("RETRY",):
        response = {"status": "processing", "message": "再試行中です..."}
    elif task_result.state in ("REVOKED",):
        response = {"status": "error", "message": "タスクは取り消されました。"}
    else:
        # 上記以外は処理継続扱い
        response = {"status": "processing", "message": "処理中..."}

    return JsonResponse(response)
