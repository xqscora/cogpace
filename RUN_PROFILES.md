# Run CogPace by competition profile

| Profile | Command | Devpost narrative |
|---------|---------|-------------------|
| Default / DSH | `streamlit run app.py` | `devpost_submission.md` |
| Youth Code social | `$env:COGPACE_PROFILE='youth_code_social'; streamlit run app.py` | `narratives/youth_code_social_devpost.md` |
| Youth Code career | `$env:COGPACE_PROFILE='youth_code_education'; streamlit run app.py` | `narratives/youth_code_education_devpost.md` |
| GitLab | `$env:COGPACE_PROFILE='gitlab_devops'; streamlit run app.py` | `narratives/gitlab_devops_devpost.md` |
| Splunk | `$env:COGPACE_PROFILE='splunk_observability'; streamlit run app.py` | set `SPLUNK_HEC_*` env vars |
| Mind the Product | `$env:COGPACE_PROFILE='mind_the_product'; streamlit run app.py` | Pendo events enabled |

**URL shortcut:** `http://localhost:8501/?profile=youth_social`

**API key:** copy `.env.example` → `.env` and set `GEMINI_API_KEY=...`
