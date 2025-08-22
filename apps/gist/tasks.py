import logging
import re

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

        # 3. タイトルと要約を正規表現で抽出
        title = "要約結果"
        summary_points = summary_text.strip()
        # 先にタイトル行を抽出（行頭の「タイトル:」を優先）
        m_title = re.search(r'(?m)^\s*タイトル:\s*(.+)\s*$', summary_text)
        if m_title:
            title = m_title.group(1).strip()
        # 「要点:」以降をサマリーとして抽出（複数行対応）
        m_points = re.search(r'(?ms)^\s*要点:\s*(.*)$', summary_text)
        if m_points:
            summary_points = m_points.group(1).strip()
        else:
            # フォールバック: 先頭行がタイトル行なら、それ以外を要点として扱う
            first_line = summary_text.splitlines()[0] if summary_text else ""
            if first_line.startswith("タイトル:"):
                summary_points = summary_text[len(first_line):].strip()

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
