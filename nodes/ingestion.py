import pandas as pd
import config
from state import AgentState


def ingestion_node(state: AgentState) -> dict:
    if state["df_csv"]:
        return {}

    df = pd.read_csv(config.DATA_PATH)

    df_csv = df.to_csv(index=False)

    schema_parts = [
        f"Shape: {df.shape[0]} rows × {df.shape[1]} columns",
        "",
        "Column dtypes:",
        df.dtypes.to_string(),
        "",
        "Null counts:",
        df.isnull().sum().to_string(),
        "",
        "First 5 rows:",
        df.head(5).to_string(index=False),
    ]
    df_schema = "\n".join(schema_parts)

    return {"df_csv": df_csv, "df_schema": df_schema}
