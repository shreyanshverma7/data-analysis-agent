import base64
import os
from e2b_code_interpreter import Sandbox
from state import AgentState

_CHART_PATH = "outputs/chart.png"


def executor_node(state: AgentState) -> dict:
    prefix = (
        "import matplotlib\n"
        "matplotlib.use('Agg')\n"
        "import os\n"
        "os.makedirs('outputs', exist_ok=True)\n"
        "import pandas as pd\n"
        "df = pd.read_csv('titanic.csv')\n"
    )
    full_code = prefix + state["generated_code"]

    with Sandbox.create(api_key=os.environ.get("E2B_API_KEY")) as sandbox:
        sandbox.files.write("titanic.csv", state["df_csv"].encode())
        execution = sandbox.run_code(full_code)

        stdout = "\n".join(execution.logs.stdout)

        if execution.error:
            error_text = f"{execution.error.name}: {execution.error.value}"
            return {"execution_output": "", "execution_error": error_text, "chart_path": ""}

        try:
            b64_exec = sandbox.run_code(
                "import base64, os\n"
                "if os.path.exists('outputs/chart.png'):\n"
                "    with open('outputs/chart.png', 'rb') as _f:\n"
                "        print(base64.b64encode(_f.read()).decode('ascii'))\n"
            )
            b64_str = "".join(b64_exec.logs.stdout).strip()
            if b64_str:
                with open(_CHART_PATH, "wb") as f:
                    f.write(base64.b64decode(b64_str))
                chart_path = os.path.abspath(_CHART_PATH)
            else:
                chart_path = ""
        except Exception:
            chart_path = ""

    return {"execution_output": stdout, "execution_error": "", "chart_path": chart_path}
