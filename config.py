import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

os.environ.setdefault("LANGCHAIN_TRACING_V2", os.getenv("LANGCHAIN_TRACING_V2", "false"))
os.environ.setdefault("LANGCHAIN_API_KEY", os.getenv("LANGCHAIN_API_KEY", ""))
os.environ.setdefault("LANGCHAIN_PROJECT", os.getenv("LANGCHAIN_PROJECT", "data-analysis-agent"))

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not set in .env")

# llama-3.3-70b-versatile: commented out — 100K tokens/day hard cap exhausted in a
# single eval run (15 questions × ~4K tokens). Scout (Llama 4 MoE, 109B total params,
# 17B active) provides 500K tokens/day and 30K TPM with comparable quality.
MODEL_NAME = "meta-llama/llama-4-scout-17b-16e-instruct"

BASE_DIR = Path(__file__).parent
DATA_PATH = BASE_DIR / "data" / "titanic.csv"
OUTPUTS_DIR = BASE_DIR / "outputs"
OUTPUTS_DIR.mkdir(exist_ok=True)

SLIDING_WINDOW = 3

def get_llm(temperature: float = 0.0) -> ChatGroq:
    return ChatGroq(
        model=MODEL_NAME,
        api_key=GROQ_API_KEY,
        temperature=temperature,
    )
