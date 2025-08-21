from django.shortcuts import render
from django.conf import settings
import requests
from bs4 import BeautifulSoup
from langchain_ollama.chat_models import ChatOllama

# LLMクライアントをモジュールレベルで初期化
llm = ChatOllama(model="qwen3:8b", base_url=settings.OLLAMA_BASE_URL)

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

                    # プロンプトを定義
                    prompt = f"""以下のテキストを日本語で要約してください。

テキスト:
{text}

要約は以下の形式で出力してください。
タイトル: 記事の内容を一行で表すタイトルを1つ生成してください。
要点: 記事の最も重要なポイントを3つを目安として、最大5つまでの箇条書きで簡潔にまとめてください。各箇条書きは100字以内にしてください。
"""
                    # モデルを呼び出して要約を生成
                    summary_result = llm.invoke(prompt)
                    context['summary'] = summary_result.content
                else:
                    context['scraped_content'] = ''

            except Exception as e:
                context['error'] = f"エラーが発生しました: {e}"
        else:
            context['error'] = "URLを入力してください。"

    return render(request, 'gist/index.html', context)
