
import json
import re


def extract_json(response_text):
    if not response_text:
        raise ValueError("AI returned an empty response.")

    cleaned_text = response_text.strip()

    cleaned_text = re.sub(
        r"^```(?:json)?",
        "",
        cleaned_text,
        flags=re.IGNORECASE
    )

    cleaned_text = re.sub(
        r"```$",
        "",
        cleaned_text
    )

    cleaned_text = cleaned_text.strip()

    try:
        return json.loads(cleaned_text)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"AI response is not valid JSON: {error}"
        ) from error
