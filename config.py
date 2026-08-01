import os
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq
from langchain_core.runnables import RunnableWithFallbacks
from langchain_litellm import ChatLiteLLM

load_dotenv()

os.environ.setdefault("LANGCHAIN_TRACING_V2", os.getenv("LANGCHAIN_TRACING_V2", "false"))
os.environ.setdefault("LANGCHAIN_API_KEY", os.getenv("LANGCHAIN_API_KEY", ""))
os.environ.setdefault("LANGCHAIN_PROJECT", os.getenv("LANGCHAIN_PROJECT", "data-analysis-agent"))

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not set in .env")

# Groq retired meta-llama/llama-4-scout-17b-16e-instruct on 2026-07-29 — it 404s on
# every call now. gpt-oss-120b (OpenAI's open-weight MoE, ~5B active params) replaces
# it: same cost/throughput band as Scout, and stronger native structured-output
# support, which matters since six nodes call .with_structured_output(). The 70B
# fallback below is a real LangChain .with_fallbacks() chain now, not a dead kwarg —
# see get_llm().
MODEL_NAME = "openai/gpt-oss-120b"

# D9: judge uses a smaller model than the agent — semantic scoring (completeness/clarity)
# does not require the same reasoning capability as generating the analysis itself.
JUDGE_MODEL = "openai/gpt-oss-20b"

BASE_DIR = Path(__file__).parent
DATA_PATH = BASE_DIR / "data" / "titanic.csv"
OUTPUTS_DIR = BASE_DIR / "outputs"
OUTPUTS_DIR.mkdir(exist_ok=True)

SLIDING_WINDOW = 3

_PRIMARY_MODEL = "groq/openai/gpt-oss-120b"
_FALLBACK_MODEL = "groq/llama-3.3-70b-versatile"


def _bare(model_id: str) -> str:
    """Strip LiteLLM's "groq/" provider prefix — Groq's models.list() returns bare ids."""
    return model_id.removeprefix("groq/")


def _fetch_groq_model_ids(timeout: float = 5) -> list[str]:
    client = Groq(api_key=GROQ_API_KEY)
    response = client.models.list(timeout=timeout)
    return [m.id for m in response.data]


# M4.0.6: one cheap check at import time so a retired model fails with a legible
# error at startup instead of a raw LiteLLM traceback surfacing deep in a graph node
# (see the Scout 17B retirement that started the M4.0 hotfix, above).
try:
    available_ids = _fetch_groq_model_ids(timeout=5)   # raises on timeout/network/5xx
except Exception as exc:
    print(f"⚠️  could not verify model availability ({type(exc).__name__}) — proceeding unchecked")
    available_ids = None

if available_ids is not None:
    primary_missing = _bare(_PRIMARY_MODEL) not in available_ids
    fallback_missing = _bare(_FALLBACK_MODEL) not in available_ids
    if primary_missing and fallback_missing:
        raise ValueError(
            f"model '{_PRIMARY_MODEL}' is no longer served by Groq; "
            f"available: {available_ids[:10]}"
        )
    elif primary_missing:
        print(f"⚠️  primary model '{_PRIMARY_MODEL}' is no longer served; "
              f"falling back to '{_FALLBACK_MODEL}'")
    elif fallback_missing:
        print(f"⚠️  fallback model '{_FALLBACK_MODEL}' is no longer served; "
              f"no protection if '{_PRIMARY_MODEL}' is later retired")

# Fallback verified 2026-07-30 (M4.0.2): forced _PRIMARY_MODEL to an invalid id,
# invoke() completed via _FALLBACK_MODEL (groq/llama-3.3-70b-versatile), confirmed
# by response_metadata.model. RunnableWithFallbacks works — this is not a dead kwarg.
def get_llm(temperature: float = 0.0) -> RunnableWithFallbacks:
    primary = ChatLiteLLM(model=_PRIMARY_MODEL, temperature=temperature)
    fallback = ChatLiteLLM(model=_FALLBACK_MODEL, temperature=temperature)
    return primary.with_fallbacks([fallback])
