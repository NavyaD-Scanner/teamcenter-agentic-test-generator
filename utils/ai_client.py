import os
from openai import OpenAI


def get_ai_client():
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY is not configured. "
            "Add it to Streamlit Secrets or your environment variables."
        )

    return OpenAI(api_key=api_key)


def call_ai(system_prompt, user_prompt, model=None):
    client = get_ai_client()

    selected_model = model or os.getenv(
        "OPENAI_MODEL",
        "gpt-4.1-mini"
    )

    response = client.chat.completions.create(
        model=selected_model,
        temperature=0.2,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ]
    )

    return response.choices[0].message.content
