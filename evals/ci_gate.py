import glob
import json
import os
import sys

files = sorted(glob.glob("evals/results_*.json"))
if not files:
    print("No results file found.")
    sys.exit(1)

with open(files[-1]) as f:
    data = json.load(f)

aggregate = data["aggregate"]
numeric_score = aggregate["numeric_score_mean"]
completeness = aggregate.get("completeness_mean", 0.0)
clarity = aggregate.get("clarity_mean", 0.0)

chart_correct = sum(
    1 for r in data["results"] if r.get("chart_correct")
)

total = len(data["results"])

summary = f"""## Eval Results ({total} questions — Titanic)
| Metric | Score |
|---|---|
| Numeric accuracy | {numeric_score:.2f} |
| Completeness | {completeness:.2f} |
| Clarity | {clarity:.2f} |
| Chart correct | {chart_correct}/{total} |"""

print(summary)

os.makedirs("evals", exist_ok=True)
with open("evals/ci_summary.txt", "w") as f:
    f.write(summary + "\n")

if numeric_score < 0.80 or chart_correct < 4:
    print(f"\nGATE FAILED: numeric={numeric_score:.2f} chart_correct={chart_correct}/{total}")
    sys.exit(1)

print(f"\nGATE PASSED")
sys.exit(0)
