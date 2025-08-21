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
            except Exception as e:
                logger.exception("Error during scraping/summarization for URL: %s", url)
                context["error"] = str(e)
        else:
            context["error"] = "URLを入力してください。"

    return render(request, "gist/index.html", context)
