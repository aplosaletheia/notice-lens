import state

from google import genai


MODEL = "gemini-3.5-flash-lite"


def process_pdf(pdf_text):

    saved_state = state.load_state()

    api_key = saved_state.get(
        "api_key",
        ""
    )

    prompt = saved_state.get(
        "prompt",
        ""
    )

    student_profile = saved_state.get(
        "student_profile",
        {}
    )

    input_text = f"""
STUDENT PROFILE
{student_profile}


PDF CONTENT
{pdf_text}
"""

    client = genai.Client(
        api_key=api_key
    )

    response = client.models.generate_content(
        model=MODEL,
        contents=input_text,
        config={
            "system_instruction": prompt,
            "response_mime_type": "application/json"
        }
    )

    return response.text