import json
import re


def extract_json(response_text: str):
    if not response_text or not response_text.strip():
        raise ValueError("The AI returned an empty response.")
    cleaned = response_text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        return json.loads(cleaned.strip())
    except json.JSONDecodeError as exc:
        start_obj, end_obj = cleaned.find("{"), cleaned.rfind("}")
        start_arr, end_arr = cleaned.find("["), cleaned.rfind("]")
        candidates = []
        if start_obj >= 0 and end_obj > start_obj:
            candidates.append(cleaned[start_obj:end_obj + 1])
        if start_arr >= 0 and end_arr > start_arr:
            candidates.append(cleaned[start_arr:end_arr + 1])
        for candidate in candidates:
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass
        raise ValueError(f"The AI response is not valid JSON: {exc}") from exc
