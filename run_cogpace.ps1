# Launch CogPace with a competition profile
param(
    [ValidateSet(
        "stem_education",
        "youth_code_social",
        "youth_code_education",
        "gitlab_devops",
        "splunk_observability",
        "mind_the_product"
    )]
    [string]$Profile = "stem_education"
)

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root
$env:COGPACE_PROFILE = $Profile
Write-Host "CogPace profile: $Profile" -ForegroundColor Cyan
Write-Host "URL shortcut: http://localhost:8501/?profile=$($Profile.Replace('_','-'))"
streamlit run app.py
