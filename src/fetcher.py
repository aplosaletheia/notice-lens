import requests


def fetch_html(url):
    """Fetch HTML content from a given URL."""

    try:
        response = requests.get(url, timeout=10)

        response.raise_for_status()

        return response.text

    except requests.RequestException:
        return ""
