from django.shortcuts import render
import requests
from bs4 import BeautifulSoup

def scrape_page(request):
    context = {}
    if request.method == 'POST':
        url = request.POST.get('url')
        if url:
            try:
                response = requests.get(url)
                response.raise_for_status()  # Raise an exception for bad status codes
                soup = BeautifulSoup(response.content, 'html.parser')
                # For simplicity, just get all the text.
                context['scraped_content'] = soup.get_text(separator='\n', strip=True)
            except requests.exceptions.RequestException as e:
                context['error'] = f"Error fetching URL: {e}"
        else:
            context['error'] = "Please enter a URL."

    return render(request, 'gist/index.html', context)
