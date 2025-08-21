from django.shortcuts import render
import requests
from bs4 import BeautifulSoup

def scrape_page(request):
    context = {}
    if request.method == 'POST':
        url = request.POST.get('url')
        if url:
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()  # ステータスコードが200番台でない場合に例外を発生させる

                soup = BeautifulSoup(response.content, 'html.parser')

                # 不要なタグ（スクリプト、スタイル、ナビゲーション、フッターなど）を削除
                for element in soup(["script", "style", "header", "footer", "nav", "aside"]):
                    element.decompose()
                
                # bodyタグからテキストのみを抽出
                if soup.body:
                    # get_text()でテキストを取得し、余分な空白や改行を整理
                    text = soup.body.get_text(separator=' ', strip=True)
                    context['scraped_content'] = text
                else:
                    context['scraped_content'] = ''

            except requests.exceptions.RequestException as e:
                context['error'] = f"URLの取得中にエラーが発生しました: {e}"
        else:
            context['error'] = "URLを入力してください。"

    return render(request, 'gist/index.html', context)
