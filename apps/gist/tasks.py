import logging

from celery import shared_task

from .services import ScrapingService, SummarizationService

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def process_url_task(self, url: str):
    """
    非同期でURLを処理するCeleryタスク。
    スクレイピング、要約を行い、進捗を更新する。
    """
    try:
        # 1. スクレイピング開始
        self.update_state(state="PROGRESS", meta={"message": "スクレイピング中..."})
        text = ScrapingService.scrape(url)
        if not text:
            # スクレイピングで内容が取れなかった場合
            return {"title": "コンテンツがありません", "summary": "このURLからは有効なコンテンツを取得できませんでした。"}

        # 2. 要約開始
        self.update_state(state="PROGRESS", meta={"message": "要約中..."})
        summarizer = SummarizationService()
        summary_text = summarizer.summarize(text)

        # 3. タイトルと要約を分割
        # "タイトル: " と "要点:" をもとに分割することを想定
        title = "要約結果"  # デフォルトタイトル
        summary_points = summary_text
        if "タイトル:" in summary_text:
            parts = summary_text.split("タイトル:", 1)
            summary_points = parts[1].strip()
            if "要点:" in parts[0]: # タイトル行に"要点:"が含まれていないことを確認
                title = parts[0].replace("要点:","").strip()
            else:
                title_line = summary_text.split('\n')[0]
                if title_line.startswith("タイトル:"):
                    title = title_line.replace("タイトル:", "").strip()
                summary_points = summary_text[len(title_line):].strip()

        # 成功時の結果を返す
        return {"title": title, "summary": summary_points}
    except ValueError as e:
        # 入力やスクレイピング中の既知のエラー
        logger.warning("Validation error in process_url_task for URL %s: %s", url, e)
        self.update_state(state="FAILURE", meta={"message": str(e)})
        # Celeryのタスクとしては成功させるが、エラーメッセージを結果として返す
        # こうすることで、フロントエンドでエラー内容をハンドリングしやすくなる
        raise Exception(str(e))
    except Exception as e:
        # 予期せぬエラー
        logger.exception("Unexpected error in process_url_task for URL: %s", url)
        # エラーメッセージを定型文にする
        error_message = "処理中に予期せぬエラーが発生しました。"
        self.update_state(state="FAILURE", meta={"message": error_message})
        raise Exception(error_message)
