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
    """
    Read a value from Streamlit Secrets first,
    then from environment variables.
    """
    try:
        import streamlit as st

        if name in st.secrets:
            value = st.secrets[name]

            if value is not None:
                return str(value).strip()

    except Exception:
        pass

    value = os.getenv(name, default)

    if isinstance(value, str):
        return value.strip()

    return value


def validate_not_placeholder(name, value):
    """
    Prevent sample values from being treated as real configuration.
    """
    if not value:
        return

    placeholder_words = [
        "replace-with",
        "your-api-key",
        "your-key",
        "your-resource",
        "your-deployment",
        "<api-key>",
        "<endpoint>",
        "<deployment>",
    ]

    normalized_value = str(value).lower()

    if any(word in normalized_value for word in placeholder_words):
        raise ValueError(
            f"{name} still contains an example or placeholder value. "
            "Update it in Streamlit App Settings -> Secrets."
        )


def get_provider_configuration():
    azure_endpoint = get_setting("AZURE_OPENAI_ENDPOINT")
    azure_key = get_setting("AZURE_OPENAI_API_KEY")
    azure_deployment = get_setting("AZURE_OPENAI_DEPLOYMENT")
    azure_api_version = get_setting(
        "AZURE_OPENAI_API_VERSION",
        "2024-10-21",
    )

    openai_key = get_setting("OPENAI_API_KEY")
    openai_model = get_setting(
        "OPENAI_MODEL",
        "gpt-4.1-mini",
    )

    for name, value in [
        ("AZURE_OPENAI_ENDPOINT", azure_endpoint),
        ("AZURE_OPENAI_API_KEY", azure_key),
        ("AZURE_OPENAI_DEPLOYMENT", azure_deployment),
        ("OPENAI_API_KEY", openai_key),
        ("OPENAI_MODEL", openai_model),
    ]:
        validate_not_placeholder(name, value)

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
            raise ValueError(
                "AZURE_OPENAI_ENDPOINT must begin with https://"
            )

        if "/openai/deployments/" in azure_endpoint:
            raise ValueError(
                "AZURE_OPENAI_ENDPOINT must contain only the Azure "
                "resource endpoint, for example: "
                "https://my-resource.openai.azure.com"
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
        "No AI provider is configured. Add either OPENAI_API_KEY "
        "or the complete Azure OpenAI configuration in "
        "Streamlit App Settings -> Secrets."
    )


def create_client():
    configuration = get_provider_configuration()

    http_client = httpx.Client(
        timeout=httpx.Timeout(
            connect=20.0,
            read=120.0,
            write=30.0,
            pool=20.0,
        ),
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

        return (
            client,
            configuration["deployment"],
            configuration,
        )

    client = OpenAI(
        api_key=configuration["api_key"],
        timeout=120.0,
        max_retries=2,
        http_client=http_client,
    )

    return (
        client,
        configuration["model"],
        configuration,
    )


def call_ai(system_prompt, user_prompt):
    client, model, configuration = create_client()

    last_error = None

    for attempt in range(1, 4):
        try:
            response = client.chat.completions.create(
                model=model,
                temperature=0.15,
                response_format={
                    "type": "json_object"
                },
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    },
                ],
            )

            content = response.choices[0].message.content

            if not content:
                raise ValueError(
                    "The AI provider returned an empty response."
                )

            return content

        except AuthenticationError as error:
            raise RuntimeError(
                "Authentication failed. Verify the API key in "
                "Streamlit App Settings -> Secrets."
            ) from error

        except RateLimitError as error:
            raise RuntimeError(
                "The AI provider rejected the request because of "
                "rate limits, quota, or insufficient API credits."
            ) from error

        except APITimeoutError as error:
            last_error = error

            if attempt < 3:
                time.sleep(attempt * 2)
                continue

            raise RuntimeError(
                "The request timed out after three attempts. "
                "Check the provider status, endpoint and network."
            ) from error

        except APIConnectionError as error:
            last_error = error

            underlying_error = (
                repr(error.__cause__)
                if error.__cause__
                else "No underlying connection detail was provided."
            )

            if attempt < 3:
                time.sleep(attempt * 2)
                continue

            provider = configuration["provider"]

            endpoint_information = (
                configuration.get(
                    "endpoint",
                    "https://api.openai.com",
                )
            )

            raise RuntimeError(
                "Could not connect to the AI provider after "
                f"three attempts. Provider: {provider}. "
                f"Endpoint: {endpoint_information}. "
                f"Underlying error: {underlying_error}. "
                "Check the endpoint, DNS, SSL certificate, "
                "firewall and Streamlit Secrets."
            ) from error

        except APIStatusError as error:
            raise RuntimeError(
                "The AI provider returned an HTTP error. "
                f"Status code: {error.status_code}. "
                f"Response: {error.response.text}"
            ) from error

        except Exception as error:
            raise RuntimeError(
                f"Unexpected AI request error: "
                f"{type(error).__name__}: {error}"
            ) from error

    raise RuntimeError(
        f"AI request failed: {last_error}"
    )
