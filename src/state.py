import os
import pickle
import copy


STATE_FILE = "notice_state.bin"
FINAL_INFO_FILE = "final_info.bin"
PDF_DIR = "pdfs"


DEFAULT_STATE = {
    # ------------------------------------------------------------
    # Student profile
    # ------------------------------------------------------------
    "student_profile": {
        "name": "",
        "institute": "",
        "course": "",
        "branch": "",
        "year": "",
        "semester": "",
        "section": "",
        "roll_number": "",
        "interests": "",
        "notices_url": "",
    },

    # ------------------------------------------------------------
    # Other application state
    # ------------------------------------------------------------
    "api_key": "",
    "prompt": """
        You are the personal assistant of a college student. You have to make sure "
        that they are aware of the notices the institute puts out. But the student is extremely busy and can't waste
        time to even think about notices unrelated to them. You have to only give them brief information about notices
        relevant to them. You have a relevance meter that you fill up (max 1, min 0) on the basis of their 'profile' and
        the pdf containing the notice. The pdf may be a picture of a physical document.
        Do not consider a notice relevant merely because it was issued by
        the student's institute. Consider the actual applicability of the
        event to the student and the geographic and organizational scope
        of the event. A large-scale event open to students beyond the
        student's institute may be relevant even if it is hosted elsewhere.
        If the event related date has passed, low relevance.
        IF RELEVACE IS LESS THAN 0.5 THEN TAKE IT AS 0.

        The output should strictly be in this format, not a single letter should go outside this JSON format.
        Include all the new lines and spaces as shown.
        The output should only be this JSON object, nothing else -

        {
            "relevance": 0.7,
            "name": "event_name.pdf",
            "event": {
            "name": "",
            "location": "",
            "registration": {
                "start_date": "",
                "start_time": "",
                "end_date": "",
                "end_time": ""
            },
            "event_start": {
                "date": "",
                "time": ""
            },
            "event_end": {
                "date": "",
                "time": ""
            },
            "category": "",
            "sub_category": ""
            },
            "summary": {
            "objective": "",
            "important_people": [],
            "scope": ""
            }
        }

        CATEGORY:
        The broad type of the event. Examples include sports, academic,
        technical, cultural, hackathon, workshop, competition, seminar, etc.

        SUB-CATEGORY:
        A more specific classification within the category. For example:
        - Sports → Cricket, Football, Basketball
        - Technical → AI/ML, Web Development, Cybersecurity
        - Academic → Conference, Olympiad, Quiz
        - Cultural → Dance, Music, Drama

        Choose the category and sub-category based on the actual nature
        and topic of the event.
        """,
    "last_notice_url": "",
}


def load_state():
    """
    Load the persistent application state.

    If the state file does not exist, return a fresh default state.
    """

    if not os.path.exists(STATE_FILE):
        return copy.deepcopy(DEFAULT_STATE)

    try:
        with open(
            STATE_FILE,
            "rb"
        ) as file:

            saved_state = pickle.load(file)

    except (
        pickle.PickleError,
        EOFError,
        OSError
    ):

        print(
            "[State] Could not read notice_state.bin."
        )

        print(
            "[State] Starting with default state."
        )

        return copy.deepcopy(DEFAULT_STATE)

    if not isinstance(
        saved_state,
        dict
    ):

        print(
            "[State] Invalid state file."
        )

        print(
            "[State] Starting with default state."
        )

        return copy.deepcopy(DEFAULT_STATE)

    # ------------------------------------------------------------
    # Add missing profile fields so older state files remain
    # compatible.
    # ------------------------------------------------------------

    if "student_profile" not in saved_state:
        saved_state["student_profile"] = {}

    for (
        field,
        default_value
    ) in DEFAULT_STATE[
        "student_profile"
    ].items():

        if field not in saved_state[
            "student_profile"
        ]:

            saved_state[
                "student_profile"
            ][field] = default_value

    # ------------------------------------------------------------
    # Add missing application-level fields.
    # ------------------------------------------------------------

    if "api_key" not in saved_state:
        saved_state["api_key"] = ""

    if "prompt" not in saved_state:
        saved_state["prompt"] = ""

    if "last_notice_url" not in saved_state:
        saved_state["last_notice_url"] = ""

    return saved_state


def save_state(saved_state):
    """
    Save the application state.
    """

    try:

        with open(
            STATE_FILE,
            "wb"
        ) as file:

            pickle.dump(
                saved_state,
                file
            )

    except OSError as error:

        print(
            f"[State] Failed to save state: {error}"
        )


def clear_state():
    """
    Completely remove the persistent application state.
    """

    if os.path.exists(
        STATE_FILE
    ):

        os.remove(
            STATE_FILE
        )

        print(
            "[State] notice_state.bin cleared."
        )

    else:

        print(
            "[State] notice_state.bin does not exist."
        )


# ----------------------------------------------------------------
# Final information
# ----------------------------------------------------------------

def load_final_info():

    if not os.path.exists(
        FINAL_INFO_FILE
    ):

        return []

    try:

        with open(
            FINAL_INFO_FILE,
            "rb"
        ) as file:

            return pickle.load(
                file
            )

    except (
        pickle.PickleError,
        EOFError,
        OSError
    ):

        print(
            "[FinalInfo] Could not read final_info.bin."
        )

        return []


def save_final_info(final_info):

    try:

        with open(
            FINAL_INFO_FILE,
            "wb"
        ) as file:

            pickle.dump(
                final_info,
                file
            )

    except OSError as error:

        print(
            f"[FinalInfo] Failed to save final information: {error}"
        )


def clear_final_info():

    if os.path.exists(
        FINAL_INFO_FILE
    ):

        os.remove(
            FINAL_INFO_FILE
        )

        print(
            "[FinalInfo] final_info.bin cleared."
        )

    else:

        print(
            "[FinalInfo] final_info.bin does not exist."
        )


# ----------------------------------------------------------------
# PDF storage
# ----------------------------------------------------------------

def ensure_pdf_directory():

    os.makedirs(
        PDF_DIR,
        exist_ok=True
    )


# ----------------------------------------------------------------
# LLM output storage
# ----------------------------------------------------------------

def store_llm_output(
    llm_output,
    source_url=""
):

    """
    Store one LLM result in final_info.bin.

    The LLM output is kept exactly as returned because the output
    format is controlled by the user-defined prompt.
    """

    final_info = load_final_info()

    entry = {
        "result": llm_output,
    }

    final_info.append(
        entry
    )

    save_final_info(
        final_info
    )

    return entry