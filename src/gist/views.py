import logging

from django.shortcuts import render

from gist.services import ScrapingService, SummarizationService

logger = logging.getLogger(__name__)


def scrape_page(request):
    context = {}
    if request.method == "POST":
        url = request.POST.get("url")
        if url:
            try:
                ScrapingService.validate_url(url)
                text = ScrapingService.scrape(url)
                context["scraped_content"] = text

                summarizer = SummarizationService()
                summary = summarizer.summarize(text)
                context["summary"] = summary
            except ValueError as e:
                # 入力エラーはユーザーにそのまま伝える
                context["error"] = str(e)
            except Exception:
                # それ以外は詳細をログにのみ出し、ユーザーには定型文を返す
                logger.exception("Error during scraping/summarization for URL: %s", url)
                context["error"] = "処理中にエラーが発生しました。時間をおいて再度お試しください。"
        else:
            context["error"] = "URLを入力してください。"

    return render(request, "gist/index.html", context)
