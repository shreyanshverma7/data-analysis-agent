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

MODEL_NAME = "llama-3.3-70b-versatile"

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
