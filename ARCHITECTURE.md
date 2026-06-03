User question
↓
[Analyst] — sees schema + last 3 exchanges → produces plan
↓
[Code-gen] — sees plan → produces pandas/matplotlib code
↓
[Executor] — injects df from CSV string, runs code via REPL
↓
[Critic] — pass → [Summarizer] → append to history → done
→ fail → back to Code-gen (max 3x)
→ escalate to Analyst (max 1x)
→ hard stop
