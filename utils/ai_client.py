import os
import time

import httpx
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    AzureOpenAI,
    OpenAI,
    RateLimitError,
)


def get_setting(name, default=None):
    """Read a setting from Streamlit Secrets, then environment variables."""
    try:
        import streamlit as st

        if name in st.secrets:
            value = st.secrets[name]
            if value is not None:
                return str(value).strip()
    except Exception:
        pass

    value = os.getenv(name, default)
    return value.strip() if isinstance(value, str) else value


def validate_not_placeholder(name, value):
    """Reject sample values accidentally copied into Streamlit Secrets."""
    if not value:
        return

    placeholders = (
        "replace-with",
        "your-api-key",
        "your-key",
        "your-resource",
        "your-deployment",
        "<api-key>",
        "<endpoint>",
        "<deployment>",
    )

    normalized = str(value).lower()
    if any(item in normalized for item in placeholders):
        raise ValueError(
            f"{name} contains a sample/placeholder value. "
            "Update it in Streamlit App Settings -> Secrets."
        )


def get_provider_configuration():
    azure_endpoint = get_setting("AZURE_OPENAI_ENDPOINT")
    azure_key = get_setting("AZURE_OPENAI_API_KEY")
    azure_deployment = get_setting("AZURE_OPENAI_DEPLOYMENT")
    azure_api_version = get_setting("AZURE_OPENAI_API_VERSION", "2024-10-21")

    openai_key = get_setting("OPENAI_API_KEY")
    openai_model = get_setting("OPENAI_MODEL", "gpt-4.1-mini")

    for name, value in (
        ("AZURE_OPENAI_ENDPOINT", azure_endpoint),
        ("AZURE_OPENAI_API_KEY", azure_key),
        ("AZURE_OPENAI_DEPLOYMENT", azure_deployment),
        ("OPENAI_API_KEY", openai_key),
        ("OPENAI_MODEL", openai_model),
    ):
        validate_not_placeholder(name, value)

    # Azure takes precedence only when a real Azure endpoint is configured.
    if azure_endpoint:
        if not azure_key:
            raise ValueError(
                "AZURE_OPENAI_ENDPOINT is configured, but "
                "AZURE_OPENAI_API_KEY is missing."
            )
        if not azure_deployment:
            raise ValueError(
                "AZURE_OPENAI_ENDPOINT is configured, but "
                "AZURE_OPENAI_DEPLOYMENT is missing."
            )
        if not azure_endpoint.startswith("https://"):
            raise ValueError("AZURE_OPENAI_ENDPOINT must begin with https://")
        if "/openai/deployments/" in azure_endpoint:
            raise ValueError(
                "AZURE_OPENAI_ENDPOINT must contain only the resource endpoint, "
                "for example https://my-resource.openai.azure.com"
            )

        return {
            "provider": "azure",
            "endpoint": azure_endpoint.rstrip("/"),
            "api_key": azure_key,
            "deployment": azure_deployment,
            "api_version": azure_api_version,
        }

    if openai_key:
        return {
            "provider": "openai",
            "api_key": openai_key,
            "model": openai_model,
        }

    raise ValueError(
        "No AI provider is configured. Add OPENAI_API_KEY, or the complete "
        "Azure OpenAI configuration, in Streamlit App Settings -> Secrets."
    )


def create_client():
    configuration = get_provider_configuration()

    http_client = httpx.Client(
        timeout=httpx.Timeout(connect=20.0, read=120.0, write=30.0, pool=20.0),
        follow_redirects=True,
    )

    if configuration["provider"] == "azure":
        client = AzureOpenAI(
            api_key=configuration["api_key"],
            azure_endpoint=configuration["endpoint"],
            api_version=configuration["api_version"],
            timeout=120.0,
            max_retries=2,
            http_client=http_client,
        )
        return client, configuration["deployment"], configuration

    client = OpenAI(
        api_key=configuration["api_key"],
        timeout=120.0,
        max_retries=2,
        http_client=http_client,
    )
    return client, configuration["model"], configuration


def test_connection():
    """Make a small provider request and return a user-safe result."""
    client, model, configuration = create_client()
    try:
        models = client.models.list()
        _ = models.data
        return {
            "success": True,
            "provider": configuration["provider"],
            "model_or_deployment": model,
            "message": "Connection successful.",
        }
    except Exception as error:
        cause = repr(error.__cause__) if error.__cause__ else str(error)
        return {
            "success": False,
            "provider": configuration["provider"],
            "model_or_deployment": model,
            "message": f"Connection failed: {type(error).__name__}: {cause}",
        }


def call_ai(system_prompt, user_prompt):
    client, model, configuration = create_client()

    for attempt in range(1, 4):
        try:
            request = {
                "model": model,
                "temperature": 0.15,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            }

            # JSON mode is supported by most current chat deployments. If a
            # provider/deployment rejects it, the APIStatusError below gives
            # the exact HTTP response so the configuration can be corrected.
            request["response_format"] = {"type": "json_object"}

            response = client.chat.completions.create(**request)
            content = response.choices[0].message.content
            if not content:
                raise ValueError("The AI provider returned an empty response.")
            return content

        except AuthenticationError as error:
            raise RuntimeError(
                "Authentication failed. Verify the API key in Streamlit Secrets."
            ) from error

        except RateLimitError as error:
            raise RuntimeError(
                "The request was rejected due to rate limits, quota, or API credits."
            ) from error

        except (APITimeoutError, APIConnectionError) as error:
            if attempt < 3:
                time.sleep(attempt * 2)
                continue

            cause = repr(error.__cause__) if error.__cause__ else str(error)
            endpoint = configuration.get("endpoint", "https://api.openai.com")
            raise RuntimeError(
                "Could not connect to the AI provider after three attempts. "
                f"Provider: {configuration['provider']}; Endpoint: {endpoint}; "
                f"Underlying error: {cause}. Check the endpoint, DNS, SSL, "
                "firewall, provider availability, and Streamlit Secrets."
            ) from error

        except APIStatusError as error:
            response_text = ""
            try:
                response_text = error.response.text
            except Exception:
                response_text = str(error)
            raise RuntimeError(
                f"AI provider HTTP error {error.status_code}: {response_text}"
            ) from error

        except Exception as error:
            raise RuntimeError(
                f"Unexpected AI request error: {type(error).__name__}: {error}"
            ) from error

    raise RuntimeError("The AI request failed after all retry attempts.")
