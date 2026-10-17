<#
  Deploy the Legal Meaning Checker to a Hugging Face Space (free, public URL).
  1. Create the Space first: https://huggingface.co/new-space  ->  name: legal-meaning-checker, SDK: Docker, template: Blank, Public.
  2. Create a token with WRITE access: https://huggingface.co/settings/tokens
  3. Run from the project folder:   .\deploy\push_to_hf_space.ps1 -Space "<your-hf-username>/legal-meaning-checker"
     When git asks for a password, paste the token.
#>
param([Parameter(Mandatory = $true)][string]$Space)
$ErrorActionPreference = "Stop"
$Repo = Split-Path -Parent $PSScriptRoot
$Tmp = Join-Path $env:TEMP ("hf-space-" + [guid]::NewGuid().ToString("N").Substring(0, 8))
git clone "https://huggingface.co/spaces/$Space" $Tmp
foreach ($d in @("api", "src", "data", "web")) { New-Item -ItemType Directory -Force -Path (Join-Path $Tmp $d) | Out-Null }
Copy-Item (Join-Path $Repo "Dockerfile") $Tmp -Force
Copy-Item (Join-Path $Repo ".dockerignore") $Tmp -Force
Copy-Item (Join-Path $Repo "deploy\hf_space\README.md") (Join-Path $Tmp "README.md") -Force
Copy-Item (Join-Path $Repo "src\legal_features.py") (Join-Path $Tmp "src") -Force
Copy-Item (Join-Path $Repo "data\enhi_lmp.jsonl") (Join-Path $Tmp "data") -Force
Copy-Item (Join-Path $Repo "web\stats640.json") (Join-Path $Tmp "web") -Force
Get-ChildItem (Join-Path $Repo "api") -Exclude "data", "model.joblib", "__pycache__" | Copy-Item -Destination (Join-Path $Tmp "api") -Recurse -Force
Push-Location $Tmp
git add -A
git commit -m "Deploy Legal Meaning Checker"
git push
Pop-Location
$User, $Name = $Space.Split("/")
Write-Host "`nDeployed. The Space builds in 2-4 minutes, then opens at: https://$($User.ToLower())-$($Name.ToLower()).hf.space" -ForegroundColor Green
