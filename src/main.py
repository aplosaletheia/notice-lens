import sys
import json
import re
from pathlib import Path
from io import BytesIO

from pypdf import PdfReader

import fetcher
import parser
import getDoc
import llm
import state


PROFILE_FIELDS = [
    "name",
    "institute",
    "course",
    "branch",
    "year",
    "semester",
    "section",
    "roll_number",
    "interests",
    "notices_url"
]


# ----------------------------------------------------------------
# Profile
# ----------------------------------------------------------------

def show_profile(saved_state):

    profile = saved_state["student_profile"]

    print("\nStudent Profile")
    print("----------------")

    for field in PROFILE_FIELDS:

        print(
            f"{field}: {profile.get(field, '')}"
        )

    print()


def edit_profile(saved_state):

    profile = saved_state["student_profile"]

    print("\nEdit Student Profile")
    print("Press Enter to keep the current value.")
    print()

    for field in PROFILE_FIELDS:

        current = profile.get(
            field,
            ""
        )

        value = input(
            f"{field} [{current}]: "
        ).strip()

        if value:
            profile[field] = value

    state.save_state(
        saved_state
    )

    print(
        "\n[State] Student profile updated."
    )


def set_profile_field(
    saved_state,
    field,
    value
):

    if field not in PROFILE_FIELDS:

        print(
            f"[State] Unknown profile field: {field}"
        )

        print(
            "[State] Available fields:"
        )

        print(
            "  " + ", ".join(PROFILE_FIELDS)
        )

        return

    saved_state[
        "student_profile"
    ][field] = value

    state.save_state(
        saved_state
    )

    print(
        f"[State] Profile field '{field}' updated."
    )


# ----------------------------------------------------------------
# API key
# ----------------------------------------------------------------

def show_api_key(saved_state):

    api_key = saved_state.get(
        "api_key",
        ""
    )

    if not api_key:

        print(
            "\n[State] API key is not configured.\n"
        )

        return

    if len(api_key) <= 11:

        masked = "*" * len(api_key)

    else:

        masked = (
            api_key[:7]
            + "..."
            + api_key[-4:]
        )

    print(
        f"\nAPI key: {masked}\n"
    )


def set_api_key(
    saved_state,
    api_key
):

    api_key = api_key.strip()

    if not api_key:

        print(
            "[State] API key cannot be empty."
        )

        return

    saved_state["api_key"] = api_key

    state.save_state(
        saved_state
    )

    print(
        "[State] API key updated."
    )


def clear_api_key(saved_state):

    saved_state["api_key"] = ""

    state.save_state(
        saved_state
    )

    print(
        "[State] API key cleared."
    )


# ----------------------------------------------------------------
# Notices
# ----------------------------------------------------------------

def show_notices_url(saved_state):

    url = saved_state[
        "student_profile"
    ].get(
        "notices_url",
        ""
    )

    if url:

        print(
            f"\nNotices page: {url}\n"
        )

    else:

        print(
            "\n[State] No notices page configured.\n"
        )


def set_notices_url(
    saved_state,
    url
):

    saved_state[
        "student_profile"
    ]["notices_url"] = url

    state.save_state(
        saved_state
    )

    print(
        f"[State] Notices page updated:\n{url}"
    )


# ----------------------------------------------------------------
# Prompt
# ----------------------------------------------------------------

def show_prompt(saved_state):

    print("\nCurrent prompt")
    print("--------------")

    print(
        saved_state.get(
            "prompt",
            ""
        )
    )

    print()


def set_prompt():

    print()
    print("Enter the new prompt.")
    print("Type END- on a new line when finished.")
    print()

    lines = []

    while True:

        line = input()

        if line == "END-":
            break

        lines.append(line)

    prompt = "\n".join(lines)

    if not prompt.strip():

        print("[Prompt] No prompt entered. Nothing changed.")
        return

    saved_state = state.load_state()

    saved_state["prompt"] = prompt

    state.save_state(saved_state)

    print("[Prompt] Prompt updated successfully.")


# ----------------------------------------------------------------
# Last notice URL
# ----------------------------------------------------------------

def show_last_url(saved_state):

    print(
        saved_state.get(
            "last_notice_url",
            ""
        )
    )


def set_last_url(
    saved_state,
    url
):

    saved_state["last_notice_url"] = url

    state.save_state(
        saved_state
    )

    print(
        "[State] Last notice URL updated."
    )


def clear_last_url(saved_state):

    saved_state["last_notice_url"] = ""

    state.save_state(
        saved_state
    )

    print(
        "[State] Last notice URL cleared."
    )


# ----------------------------------------------------------------
# State
# ----------------------------------------------------------------

def show_state(saved_state):

    print(
        "\n================ STATE ================\n"
    )

    show_profile(
        saved_state
    )

    print("API Key")
    print("-------")

    show_api_key(
        saved_state
    )

    print("Prompt")
    print("------")

    print(
        saved_state.get(
            "prompt",
            ""
        )
    )

    print(
        "\nLast Notice URL"
    )

    print(
        "----------------"
    )

    print(
        saved_state.get(
            "last_notice_url",
            ""
        )
    )

    print(
        "\n========================================\n"
    )


def clear_state_command():

    print()
    print("WARNING")
    print("----------------------------------------")
    print("This will erase:")
    print("  - Student profile")
    print("  - API key")
    print("  - Prompt")
    print("  - Last notice URL")
    print("  - All other stored application state")
    print("----------------------------------------")
    print()

    confirmation = input(
        "Type CLEAR to continue: "
    ).strip()

    if confirmation != "CLEAR":

        print(
            "[State] Clear cancelled."
        )

        return

    confirmation_2 = input(
        "Type CLEAR again to permanently confirm: "
    ).strip()

    if confirmation_2 != "CLEAR":

        print(
            "[State] Clear cancelled."
        )

        return

    state.clear_state()

    print(
        "[State] State reset successfully."
    )


# ----------------------------------------------------------------
# PDF handling
# ----------------------------------------------------------------

def extract_pdf_text(pdf_bytes):

    reader = PdfReader(
        BytesIO(pdf_bytes)
    )

    pages = []

    for page in reader.pages:

        text = page.extract_text()

        if text:
            pages.append(text)

    return "\n".join(
        pages
    )


def sanitize_filename(name):

    name = str(
        name or ""
    ).strip()

    if not name:
        name = "document.pdf"

    name = re.sub(
        r'[<>:"/\\|?*]',
        "_",
        name
    )

    name = name.strip(
        " ."
    )

    if not name:
        name = "document.pdf"

    if not name.lower().endswith(".pdf"):
        name += ".pdf"

    return name


def save_relevant_pdf(document, name):

    state.ensure_pdf_directory()

    pdf_directory = Path(
        state.PDF_DIR
    )

    filename = sanitize_filename(
        document.get(
            name
        )
    )

    destination = (
        pdf_directory / filename
    )

    if destination.exists():

        stem = destination.stem
        suffix = destination.suffix

        counter = 2

        while True:

            candidate = (
                pdf_directory
                / f"{stem}_{counter}{suffix}"
            )

            if not candidate.exists():

                destination = candidate
                break

            counter += 1

    with open(
        destination,
        "wb"
    ) as file:

        file.write(
            document["content"]
        )

    return destination


# ----------------------------------------------------------------
# LLM processing
# ----------------------------------------------------------------

def process_documents(documents):

    relevant_count = 0
    irrelevant_count = 0
    failed_count = 0

    total = len(
        documents
    )

    for index, document in enumerate(
        documents,
        start=1
    ):

        print()
        print(
            "------------------------------------------------"
        )

        print(
            f"[LLM] Processing document "
            f"{index}/{total}"
        )

        print(
            f"[LLM] Name: "
            f"{document.get('name', '')}"
        )

        try:

            # ----------------------------------------------------
            # Extract text from this PDF.
            # ----------------------------------------------------

            pdf_text = extract_pdf_text(
                document["content"]
            )

            if not pdf_text.strip():

                print(
                    "[LLM] PDF contained no extractable text."
                )

                failed_count += 1

                continue

            print(
                "[LLM] PDF text extracted."
            )

            # ----------------------------------------------------
            # Process THIS document.
            #
            # This is deliberately inside the loop so every
            # retrieved document gets sent to the LLM.
            # ----------------------------------------------------

            llm_output = llm.process_pdf(
                pdf_text
            )

            print(
                "[LLM] Response received."
            )

            try:

                output = json.loads(
                    llm_output
                )

            except json.JSONDecodeError:

                print(
                    "[LLM] Invalid JSON returned."
                )

                print(
                    "[LLM] Document will not be stored."
                )

                failed_count += 1

                continue

            relevance = output.get(
                "relevance",
                0
            )

            print(
                f"[LLM] Relevance: {relevance}"
            )

            try:

                is_relevant = (
                    float(relevance) != 0
                )

            except (
                TypeError,
                ValueError
            ):

                print(
                    "[LLM] Invalid relevance value."
                )

                failed_count += 1

                continue

            if not is_relevant:

                print(
                    "[LLM] Document is irrelevant."
                )

                irrelevant_count += 1

                continue

            # ----------------------------------------------------
            # Relevant:
            #   1. Store LLM result.
            #   2. Save corresponding PDF.
            # ----------------------------------------------------

            print(
                "[LLM] Document is relevant."
            )

            state.store_llm_output(
                llm_output
            )

            print(
                "[LLM] Output stored."
            )

            pdf_path = save_relevant_pdf(
                document,
                output.get("name", sanitize_filename(name))
            )

            print(
                f"[LLM] PDF saved: {pdf_path}"
            )

            relevant_count += 1

        except Exception as error:

            print(
                f"[LLM] Failed to process document: "
                f"{error}"
            )

            failed_count += 1

            # Continue with the next document.
            continue

    print()
    print(
        "================================================"
    )

    print(
        "[LLM] Processing complete."
    )

    print(
        f"[LLM] Relevant:   {relevant_count}"
    )

    print(
        f"[LLM] Irrelevant: {irrelevant_count}"
    )

    print(
        f"[LLM] Failed:     {failed_count}"
    )

    print(
        "================================================"
    )


# ----------------------------------------------------------------
# Check for new notices
# ----------------------------------------------------------------

def check_for_new_notices(saved_state):

    notices_url = saved_state[
        "student_profile"
    ].get(
        "notices_url",
        ""
    )

    if not notices_url:

        print(
            "[Main] No notices page configured."
        )

        print(
            "[Main] Set one with:"
        )

        print(
            '  python main.py notices set "<URL>"'
        )

        return

    print(
        f"[Main] Checking notices page:\n"
        f"{notices_url}"
    )

    html = fetcher.fetch_html(
        notices_url
    )

    if not html:

        print(
            "[Main] Failed to fetch notices page."
        )

        return

    notice_urls = parser.parse_notice_links(
        html
    )

    if not notice_urls:

        print(
            "[Main] No notice URLs found."
        )

        return

    print(
        f"[Main] Notices found: "
        f"{len(notice_urls)}"
    )

    state.ensure_pdf_directory()

    documents, failed_notices = (
        getDoc.documentRetrieval(
            notice_urls,
            notices_url
        )
    )

    print(
        f"[Main] Documents retrieved: "
        f"{len(documents)}"
    )

    if documents:

        process_documents(
            documents
        )

    else:

        print(
            "[Main] No documents to process."
        )

    # getDoc owns the last_notice_url update.
    state.load_state()

    if failed_notices:

        print(
            "\n[Main] Document retrieval failures:"
        )

        for failure in failed_notices:

            if isinstance(
                failure,
                dict
            ):

                url = failure.get(
                    "url",
                    ""
                )

                reason = failure.get(
                    "reason",
                    "unknown"
                )

                name = failure.get(
                    "name",
                    ""
                )

                if name:

                    print(
                        f"  - {name}: "
                        f"{url} ({reason})"
                    )

                else:

                    print(
                        f"  - {url} ({reason})"
                    )

            else:

                print(
                    f"  - {failure}"
                )

        print(
            "\n[Main] These documents will not be "
            "automatically retried."
        )

        print(
            "[Main] Handle them manually if necessary."
        )


# ----------------------------------------------------------------
# Help
# ----------------------------------------------------------------

def print_help():

    print("""
EVENTS HELPER
──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

GENERAL                                 NOTICES                                 PROFILE
  help | <none>                           notices | notices check                 profile | profile show | profile edit
                                          notices show | notices set <url>        profile set <field> <value>

PROMPT                                  API KEY                                 LAST URL
  prompt | prompt show | prompt set       api-key | api-key show                  last-url | last-url show
                                          api-key set <key> | api-key clear        last-url set <url> | last-url clear

STATE                                   FINAL
  state | state show | state clear        final | final show | final clear

──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
""")


# ----------------------------------------------------------------
# CLI command handling
# ----------------------------------------------------------------

def handle_command(argv):

    saved_state = state.load_state()

    # ------------------------------------------------------------
    # No command = check for new notices.
    # ------------------------------------------------------------

    if len(argv) == 1:

        check_for_new_notices(
            saved_state
        )

        return

    command = argv[1]

    # ============================================================
    # help
    # ============================================================

    if command == "help":

        print_help()

        return

    # ============================================================
    # state
    # ============================================================

    if command == "state":

        if (
            len(argv) == 2
            or argv[2] == "show"
        ):

            show_state(
                saved_state
            )

            return

        if argv[2] == "clear":

            clear_state_command()

            return

    # ============================================================
    # profile
    # ============================================================

    if command == "profile":

        if (
            len(argv) == 2
            or argv[2] == "show"
        ):

            show_profile(
                saved_state
            )

            return

        if argv[2] == "edit":

            edit_profile(
                saved_state
            )

            return

        if argv[2] == "set":

            if len(argv) < 5:

                print(
                    "Usage: "
                    "python main.py profile set "
                    "<field> <value>"
                )

                return

            field = argv[3]

            value = " ".join(
                argv[4:]
            )

            set_profile_field(
                saved_state,
                field,
                value
            )

            return

    # ============================================================
    # API key
    # ============================================================

    if command == "api-key":

        if (
            len(argv) == 2
            or argv[2] == "show"
        ):

            show_api_key(
                saved_state
            )

            return

        if argv[2] == "set":

            if len(argv) < 4:

                print(
                    "Usage: "
                    "python main.py api-key set <key>"
                )

                return

            set_api_key(
                saved_state,
                argv[3]
            )

            return

        if argv[2] == "clear":

            clear_api_key(
                saved_state
            )

            return

    # ============================================================
    # notices
    # ============================================================

    if command == "notices":

        if (
            len(argv) == 2
            or argv[2] == "check"
        ):

            check_for_new_notices(
                saved_state
            )

            return

        if argv[2] == "show":

            show_notices_url(
                saved_state
            )

            return

        if argv[2] == "set":

            if len(argv) < 4:

                print(
                    'Usage: '
                    'python main.py notices set "<URL>"'
                )

                return

            set_notices_url(
                saved_state,
                argv[3]
            )

            return

    # ============================================================
    # prompt
    # ============================================================

    if command == "prompt":

        if (
            len(argv) == 2
            or argv[2] == "show"
        ):

            show_prompt(
                saved_state
            )

            return

        if argv[2] == "set":

            set_prompt(
                
            )

            return

    # ============================================================
    # last notice URL
    # ============================================================

    if command == "last-url":

        if (
            len(argv) == 2
            or argv[2] == "show"
        ):

            show_last_url(
                saved_state
            )

            return

        if argv[2] == "set":

            if len(argv) < 4:

                print(
                    "Usage: "
                    "python main.py last-url set <url>"
                )

                return

            set_last_url(
                saved_state,
                argv[3]
            )

            return

        if argv[2] == "clear":

            clear_last_url(
                saved_state
            )

            return

    # ============================================================
    # final information
    # ============================================================

    if command == "final":
   
       if (
           len(argv) == 2
           or argv[2] == "show"
       ):
   
           final_info = state.load_final_info()
   
           print(
               f"\n[FinalInfo] "
               f"{len(final_info)} entries stored."
           )
   
           for index, item in enumerate(
               final_info,
               start=1
           ):
   
               result = item.get(
                   "result",
                   ""
               )
   
               try:
                   data = json.loads(result)
   
               except (
                   json.JSONDecodeError,
                   TypeError
               ):
   
                   print()
                   print(
                       f"--- Result {index} ---"
                   )
   
                   print(
                       result
                   )
   
                   continue
   
               event = data.get(
                   "event",
                   {}
               )
   
               summary = data.get(
                   "summary",
                   {}
               )
   
               print()
               print(
                   f"--- Result {index} ---"
               )
   
               print(
                   f"Name         : "
                   f"{event.get('name', 'Unnamed Event')}"
               )
   
               print(
                   f"Location     : "
                   f"{event.get('location', '')}"
               )
   
               print(
                   f"Category     : "
                   f"{event.get('category', '')}"
               )
   
               print(
                   f"Sub-category : "
                   f"{event.get('sub_category', '')}"
               )
   
               registration = event.get(
                   "registration",
                   {}
               )
   
               print(
                   "Registration : "
                   f"{registration.get('start_date', '')} "
                   f"{registration.get('start_time', '')}"
                   " → "
                   f"{registration.get('end_date', '')} "
                   f"{registration.get('end_time', '')}"
               )
   
               event_start = event.get(
                   "event_start",
                   {}
               )
   
               event_end = event.get(
                   "event_end",
                   {}
               )
   
               print(
                   "Event        : "
                   f"{event_start.get('date', '')} "
                   f"{event_start.get('time', '')}"
                   " → "
                   f"{event_end.get('date', '')} "
                   f"{event_end.get('time', '')}"
               )
   
               print(
                   f"Objective    : "
                   f"{summary.get('objective', '')}"
               )
   
               print(
                   f"Scope        : "
                   f"{summary.get('scope', '')}"
               )
   
               people = summary.get(
                   "important_people",
                   []
               )
   
               if people:
   
                   print(
                       "Important    :"
                   )
   
                   for person in people:
   
                       print(
                           f"  • {person}"
                       )
   
               print(
                   f"PDF          : "
                   f"{data.get('name', '')}"
               )
   
               print(
                   f"Relevance    : "
                   f"{data.get('relevance', '')}"
               )
   
           return
   
       if argv[2] == "clear":
   
           state.clear_final_info()
   
           return

    # ============================================================
    # Unknown command
    # ============================================================

    print(
        f"Unknown command: {command}"
    )

    print(
        "Run 'python main.py help' "
        "for available commands."
    )


# ----------------------------------------------------------------
# Main
# ----------------------------------------------------------------

if __name__ == "__main__":

    handle_command(
        sys.argv
    )