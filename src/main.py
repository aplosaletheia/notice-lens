import fetcher
import parser
import getDoc


# Eventually this should be loaded from persistent storage.
last_notice_url = ""


def get_new_notice_urls(notice_urls, last_notice_url):
    """
    Get notices that appeared after the last processed notice.

    The notice URL is the unique identifier.
    Notice names/titles are not used.
    """

    new_notice_urls = []
    seen_urls = set()

    for notice in notice_urls:

        url = notice.get("url")

        if not url:
            continue

        # Prevent the same URL appearing twice in one scrape.
        if url in seen_urls:
            continue

        seen_urls.add(url)

        # We have reached a notice that was already processed.
        if url == last_notice_url:
            break

        new_notice_urls.append(notice)

    return new_notice_urls


if __name__ == "__main__":

    hp_url = input("Enter the URL: ").strip()

    html = fetcher.fetch_html(hp_url)

    notice_urls = parser.parse_notice_links(html)

    if not notice_urls:

        print("[Main] No notice URLs found.")
        print("[Main] Going directly to browser retrieval.")

        documents, failed_urls = getDoc.documentRetrieval(
            [],
            hp_url
        )

    else:

        new_notice_urls = get_new_notice_urls(
            notice_urls,
            last_notice_url
        )

        print(f"[Main] Notices found: {len(notice_urls)}")
        print(f"[Main] New notices: {len(new_notice_urls)}")

        if not new_notice_urls:

            print("[Main] No new notices.")

            documents = []
            failed_urls = []

        else:

            documents, failed_urls = getDoc.documentRetrieval(
                new_notice_urls,
                hp_url
            )

            # ----------------------------------------------------
            # IMPORTANT:
            # Every notice we attempted is now considered checked.
            #
            # A failed document is NOT retried automatically.
            # It will be reported through failed_urls so that
            # the event/document can be entered manually.
            # ----------------------------------------------------

            last_notice_url = new_notice_urls[0]["url"]

            if failed_urls:

                print("\n[Main] The following documents failed:")

                for url in failed_urls:
                    print(f"  - {url}")

                print(
                    "\n[Main] These will not be checked again automatically."
                )
                print(
                    "[Main] You can manually enter the PDF or event details."
                )