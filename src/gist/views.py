from django.shortcuts import render
from django.conf import settings
import requests
from bs4 import BeautifulSoup
from langchain_ollama import ChatOllama
import logging
from urllib.parse import urlparse
import socket
import ipaddress

# LLMクライアントをモジュールレベルで初期化
llm = ChatOllama(model=settings.OLLAMA_MODEL, base_url=settings.OLLAMA_BASE_URL)

def scrape_page(request):
    context = {}
    if request.method == 'POST':
        url = request.POST.get('url')
        if url:
            try:
                # URL 検証（http/https のみ許可）
                parsed = urlparse(url)
                if parsed.scheme not in ("http", "https"):
                    raise ValueError("URLは http/https のみ対応しています。")
                if not parsed.hostname:
                    raise ValueError("URLのホスト名が不正です。")

                # DNS 解決してプライベート/ループバック等をブロック
                def _is_private_host(host: str) -> bool:
                    addrs = set()
                    for family in (socket.AF_INET, socket.AF_INET6):
                        try:
                            for info in socket.getaddrinfo(host, None, family):
                                addrs.add(info[4][0])
                        except socket.gaierror:
                            continue
                    for addr in addrs:
                        ip = ipaddress.ip_address(addr.split('%')[0])
                        if (ip.is_private or ip.is_loopback or ip.is_link_local
                            or ip.is_reserved or ip.is_multicast or ip.is_unspecified):
                            return True
                    return False
                if _is_private_host(parsed.hostname):
                    raise ValueError("指定のホストは許可されていません。")

                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                # リダイレクトは無効化し、タイムアウトは (接続, 読み取り) で指定
                response = requests.get(url, headers=headers, timeout=(5, 15), allow_redirects=False)
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
                logging.getLogger(__name__).exception("スクレイピング/要約処理でエラー")
                context['error'] = "エラーが発生しました。しばらくしてからお試しください。"
        else:
            context['error'] = "URLを入力してください。"

    return render(request, 'gist/index.html', context)
