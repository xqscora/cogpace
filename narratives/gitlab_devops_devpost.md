# CogPace — GitLab Transcend narrative

**Run:** `COGPACE_PROFILE=gitlab_devops streamlit run app.py`

Attention telemetry as DevOps artifact. Each answer emits JSON: `session_id`, `attention_state`, `f_att`, `r`, `S`.

Local logs: `session_logs/{session_id}.jsonl`  
Export summary: `session_logs/{session_id}_summary.json`

GitLab Duo can explain MRs that change MFA thresholds in `mfa_attention.py` — zero preset adaptation in app layer.
