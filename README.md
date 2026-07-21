# Teamcenter Agentic AI Test Case Generator

A Streamlit application that uses four AI stages to analyze Teamcenter requirements and generate realistic, traceable test cases:

1. Requirement Analyzer Agent
2. Coverage Planning Agent
3. Test Case Generator Agent
4. Independent Review and Correction Agent

## GitHub upload

Upload the extracted project files while preserving the folder structure. Do not upload only the ZIP if you want GitHub/Streamlit to run the application.

## Configure secrets

For Streamlit Community Cloud, open **App settings → Secrets** and add:

```toml
OPENAI_API_KEY = "your-key"
OPENAI_MODEL = "your-supported-model"
```

For Azure OpenAI, use:

```toml
AZURE_OPENAI_ENDPOINT = "https://your-resource.openai.azure.com/"
AZURE_OPENAI_API_KEY = "your-key"
AZURE_OPENAI_DEPLOYMENT = "your-deployment-name"
AZURE_OPENAI_API_VERSION = "2024-10-21"
```

Do not configure both providers at once unless you intend Azure OpenAI to take precedence.

## Local run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Streamlit deployment

- Repository: this repository
- Branch: `main`
- Main file: `app.py`
- Add secrets before testing generation.

## Customize Teamcenter values

Edit `config/teamcenter_config.json` to use the exact business object types, datasets, workflows, performer slots, roles and statuses from your environment.

## Security

Never commit `.env` or `.streamlit/secrets.toml`. Both are excluded by `.gitignore`.
