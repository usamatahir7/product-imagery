import os


def get_openai_api_key() -> str:
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if key:
        return key
    raise RuntimeError(
        "OPENAI_API_KEY is not set. "
        "Local: copy .env.example to .env and add your key. "
        "Streamlit Cloud: add OPENAI_API_KEY in App settings → Secrets."
    )
