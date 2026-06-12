# CogPace × Splunk — Architecture (Agentic Ops / Observability)

See also: [`docs/architecture_splunk.md`](docs/architecture_splunk.md)

## Problem

Learning platforms rarely export **cognitive telemetry**. ITOps teams see server metrics; educators see quiz scores — not the *attention collapse* signal before a student disengages.

## Solution

CogPace emits structured **attention state events** to Splunk via HTTP Event Collector (HEC). Security/SRE teams can correlate F_att drops with infra incidents; educators get observability dashboards.

```
┌─────────────┐     response      ┌──────────────────┐
│   Student   │ ────────────────► │  CogPace (Streamlit) │
└─────────────┘                   │  mfa_attention.py    │
                                  │  F_att = S / r²      │
                                  └──────────┬───────────┘
                                             │ attention_event JSON
                                             ▼
                                  ┌──────────────────┐
                                  │ integrations/    │
                                  │ splunk_hec.py    │
                                  └──────────┬───────┘
                                             │ HTTPS POST
                                             ▼
                                  ┌──────────────────┐
                                  │ Splunk Enterprise│
                                  │ HEC :8088        │
                                  └──────────┬───────┘
                                             │
                                             ▼
                                  ┌──────────────────┐
                                  │ SPL + Dashboards │
                                  │ (anomaly alerts) │
                                  └──────────────────┘
```

## Event schema (`sourcetype=cogpace:attention:v1`)

| Field | Type | Description |
|-------|------|-------------|
| `session_id` | string | Streamlit session |
| `question_id` | string | Bank item id |
| `attention_state` | enum | OPTIMAL / UNDERLOADED / APPROACHING / OVERLOADED |
| `f_att` | float | MFA field strength |
| `r` | float | Psychological distance proxy |
| `S` | float | Motivation / streak field |
| `response_ms` | int | Latency |
| `correct` | bool | Answer correctness |

## Setup

```bash
export SPLUNK_HEC_URL=https://your-splunk:8088
export SPLUNK_HEC_TOKEN=your-hec-token
streamlit run app.py
```
