from typing import Literal

from pydantic import BaseModel, Field


class CriticVerdict(BaseModel):
    verdict: Literal["pass", "retry"] = Field(description="Whether the execution output adequately answers the question.")
    reason: str = Field(description="One-sentence explanation for the verdict.")


class AnalysisPlan(BaseModel):
    steps: list[str] = Field(description="Ordered list of analysis steps to execute against the dataframe.")
    expected_output_type: Literal["numeric", "chart", "both"] = Field(description="Whether the output will be a numeric result, a chart, or both.")


class NarrativeOutput(BaseModel):
    interpretation: str = Field(description="Plain-language interpretation of the statistical findings.")
    key_numbers: list[str] = Field(description="List of the most important numeric values extracted from the stats output.")


class SynthesisOutput(BaseModel):
    answer: str = Field(description="Final natural-language answer combining stats, chart, and narrative into a cohesive response.")
    has_chart: bool = Field(description="Whether a chart was successfully generated and is available.")
    confidence: Literal["high", "medium", "low"] = Field(description="Confidence level based on data completeness and specialist success.")
