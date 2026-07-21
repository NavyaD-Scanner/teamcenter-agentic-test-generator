import os
from openai import OpenAI, AzureOpenAI


def _get_setting(name, default=None):
    try:
        import streamlit as st
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return os.getenv(name, default)


def call_ai(system_prompt: str, user_prompt: str):
    azure_endpoint = _get_setting("AZURE_OPENAI_ENDPOINT")
    if azure_endpoint:
        key = _get_setting("AZURE_OPENAI_API_KEY")
        deployment = _get_setting("AZURE_OPENAI_DEPLOYMENT")
        api_version = _get_setting("AZURE_OPENAI_API_VERSION", "2024-10-21")
        if not key or not deployment:
            raise ValueError("Configure AZURE_OPENAI_API_KEY and AZURE_OPENAI_DEPLOYMENT.")
        client = AzureOpenAI(api_key=key, azure_endpoint=azure_endpoint, api_version=api_version)
        model = deployment
    else:
        key = _get_setting("OPENAI_API_KEY")
        if not key:
            raise ValueError("Configure OPENAI_API_KEY in Streamlit Secrets or environment variables.")
        client = OpenAI(api_key=key)
        model = _get_setting("OPENAI_MODEL", "gpt-4.1-mini")

    response = client.chat.completions.create(
        model=model,
        temperature=0.15,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content
