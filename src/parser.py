from bs4 import BeautifulSoup


def parse_notice_links(html):
    """
    Parse notice links from the given HTML.

    Links inside common UI/navigation sections are ignored.

    Args:
        html (str): HTML content of the notices webpage.

    Returns:
        list[dict]: List of notices, each containing:
                    - name: text associated with the link
                    - url: URL from the href attribute
    """

    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")

    notices = []

    for link in soup.find_all("a", href=True):

        # Ignore links inside common UI/navigation sections.
        if link.find_parent(
            ["header", "nav", "footer", "aside"]
        ):
            continue

        name = link.get_text(" ", strip=True)
        url = str(link["href"]).strip()

        notices.append({
            "name": name,
            "url": url
        })

    return notices