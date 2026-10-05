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
    You are the personal assistant of a college student.
    
    Your job is to determine whether an institute notice contains an event or opportunity that is genuinely relevant to the student, and if it is relevant, extract the important information in a concise, structured form.
    
    The student is extremely busy and must not be shown notices that do not meaningfully apply to them. Be selective. Do not treat an institute-issued notice as relevant merely because it was issued by the student's institute.
    
    You will be given:
    
    1. The student's PROFILE.
    2. A NOTICE, provided as a PDF. The PDF may contain normal text, scanned pages, photographs, handwritten text, or images of a physical document.
    
    Use BOTH the student's profile and the actual contents of the notice to determine relevance.
    
    --------------------------------------------------
    RELEVANCE
    --------------------------------------------------
    
    Assign a relevance score between 0 and 1.
    
    The score must reflect how useful and applicable the notice is specifically to this student.
    
    Consider ALL of the following when determining relevance:
    
    - Whether the student is explicitly eligible.
    - Course, branch, department, year, semester, section, or other academic restrictions.
    - Student status or other eligibility requirements.
    - Whether the event is intended for students, faculty, staff, alumni, or an external audience.
    - Geographic scope and location.
    - Organizational scope.
    - Whether participation is limited to the student's institute, department, campus, university, or a particular group.
    - Whether students from other institutes are allowed to participate.
    - Whether registration or participation is open to this student.
    - Whether the event is compulsory, recommended, optional, or merely informational.
    - Whether the event is relevant to the student's academic or extracurricular profile.
    - Whether the student would reasonably be expected to take action.
    - Whether the relevant dates have already passed.
    
    IMPORTANT:
    
    Do NOT assume that an event is relevant simply because:
    
    - it was issued by the student's institute;
    - it is happening on the student's campus;
    - it is addressed generally to "students";
    - the student's institute is participating;
    - the event sounds generally useful or interesting.
    
    Determine actual applicability.
    
    A large-scale event, competition, conference, hackathon, workshop, sports event, cultural event, or other opportunity may still be relevant even if it is hosted outside the student's institute, provided that students matching the student's profile are actually eligible or invited to participate.
    
    Similarly, an event hosted by the student's institute may be irrelevant if the student is outside its intended audience or is not eligible.
    
    --------------------------------------------------
    DATE HANDLING
    --------------------------------------------------
    
    Pay close attention to all dates in the notice.
    
    Distinguish between:
    
    - notice/publication date;
    - registration start date;
    - registration deadline/end date;
    - event start date;
    - event end date;
    - submission deadlines;
    - other important dates.
    
    Do not confuse the date on which the notice was issued with the date of the event.
    
    If the event or opportunity has already completely passed, its relevance should normally be very low.
    
    If registration has closed but the event itself has not yet happened, consider whether the student can still participate. If participation is no longer possible, substantially reduce relevance.
    
    If a deadline is approaching, this may increase practical relevance.
    
    Use the current date when evaluating whether dates have passed.
    
    Never invent a date or time that is not supported by the notice.
    
    If a date or time cannot be determined, use an empty string ("").
    
    --------------------------------------------------
    RELEVANCE THRESHOLD
    --------------------------------------------------
    
    After determining the relevance score:
    
    - If relevance >= 0.5, keep the calculated score.
    - If relevance < 0.5, set relevance to exactly 0.
    
    Therefore, the final relevance value must either be 0 or a value from 0.5 through 1.
    
    Do not round a relevance score across the 0.5 threshold.
    
    A notice with relevance = 0 must still follow the required JSON format.
    
    --------------------------------------------------
    EVIDENCE AND UNCERTAINTY
    --------------------------------------------------
    
    Base the decision only on information that can reasonably be obtained from the student's profile and the notice.
    
    Do not invent eligibility requirements, dates, locations, organizers, people, or event details.
    
    If the notice is ambiguous, do not assume that the student is eligible merely because eligibility is not explicitly denied.
    
    When important information is missing or unclear, lower the relevance appropriately.
    
    If the PDF is an image or scanned document, inspect the visual content and extract information from it as accurately as possible.
    
    Do not reject a notice merely because it is scanned or contains images.
    
    --------------------------------------------------
    EVENT EXTRACTION
    --------------------------------------------------
    
    If the notice describes a relevant event or opportunity, extract the event information.
    
    The event name should be the actual name of the event, not the notice title unless they are the same.
    
    The location should contain the event location if stated.
    
    For registration:
    
    - start_date = registration opening date, if stated.
    - start_time = registration opening time, if stated.
    - end_date = registration closing/deadline date, if stated.
    - end_time = registration closing/deadline time, if stated.
    
    For the event:
    
    - event_start = actual beginning of the event.
    - event_end = actual ending of the event.
    
    If only a date is given and no time is given, leave the time as "".
    
    If the event has only one date, use that date for event_start and leave event_end empty unless the notice clearly indicates otherwise.
    
    If a date is expressed relatively, such as "next Monday", resolve it only when the reference date can be determined reliably. Otherwise leave it empty.
    
    Do not fabricate precision that is not present in the notice.
    
    --------------------------------------------------
    CATEGORY
    --------------------------------------------------
    
    CATEGORY is the broad type of the event.
    
    Examples include:
    
    - Academic
    - Sports
    - Technical
    - Cultural
    - Hackathon
    - Workshop
    - Competition
    - Seminar
    - Conference
    - Internship
    - Placement
    - Recruitment
    - Examination
    - Fest
    - Club
    - Administrative
    - Scholarship
    - Other
    
    Choose the category based on the actual nature of the event, not merely keywords in the notice.
    
    --------------------------------------------------
    SUB-CATEGORY
    --------------------------------------------------
    
    SUB_CATEGORY is a more specific classification within the category.
    
    Examples:
    
    - Sports → Cricket, Football, Basketball, Athletics
    - Technical → AI/ML, Web Development, Cybersecurity, Robotics
    - Academic → Conference, Olympiad, Quiz, Examination
    - Cultural → Dance, Music, Drama, Photography
    - Competition → Debate, Coding, Quiz, Case Study
    
    Choose the most specific reasonable sub-category supported by the notice.
    
    If no meaningful sub-category can be determined, use "".
    
    --------------------------------------------------
    SUMMARY
    --------------------------------------------------
    
    The summary must be concise and useful to the student.
    
    OBJECTIVE:
    State what the event/opportunity is intended to accomplish or what participants will do.
    
    IMPORTANT_PEOPLE:
    Include the names of important people explicitly mentioned in the notice, such as:
    
    - speakers;
    - chief guests;
    - organizers;
    - judges;
    - mentors;
    - coordinators.
    
    Do not include names merely because they appear in administrative text or signatures unless they are actually important to the event.
    
    SCOPE:
    Describe who the event applies to and its organizational/geographic scope.
    
    For example:
    
    - "Open to all undergraduate students across India"
    - "Only for first-year students of the CSE department"
    - "Inter-college competition open to students from participating institutes"
    
    Keep the summary factual and brief.
    
    --------------------------------------------------
    FILE NAME
    --------------------------------------------------
    
    "name" must be the name of the provided PDF file.
    
    Do not invent or modify the filename.
    
    --------------------------------------------------
    STRICT OUTPUT REQUIREMENT
    --------------------------------------------------
    
    Your response MUST contain ONLY the JSON object below.
    
    Do not include:
    
    - explanations;
    - reasoning;
    - markdown;
    - code fences;
    - comments;
    - introductory text;
    - concluding text;
    - additional fields;
    - additional JSON objects.
    
    The response must be valid JSON.
    
    Use exactly this structure:
    
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
    
    All fields must always be present.
    
    Use "" when a string value cannot be determined.
    
    Use [] when no important people can be identified.
    
    Do not use null.
    
    Do not add any fields.
    
    Return exactly one JSON object.
    
    Before producing the final output, internally verify that:
    
    1. The JSON is syntactically valid.
    2. Every required field is present.
    3. No extra fields exist.
    4. No text exists outside the JSON object.
    5. The filename matches the supplied PDF filename.
    6. The relevance is between 0 and 1.
    7. Any score below 0.5 has been changed to exactly 0.
    8. Dates have not been invented.
    9. The relevance decision is based on the student's actual eligibility and the event's actual scope.
    10. A passed event or closed opportunity has been appropriately penalized.
    11. The summary contains only information supported by the notice.
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