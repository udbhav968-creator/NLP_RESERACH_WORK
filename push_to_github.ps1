<#
  Pushes the EnHi-LMP project (code + data + results + slides + papers) to
  https://github.com/udbhav968-creator/NLP_RESERACH_WORK
  Usage: put this script next to EnHi-LMP-JudgeBERT_code.zip, then in PowerShell:
      Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
      .\push_to_github.ps1
  Needs Git for Windows (https://git-scm.com/download/win). The first push opens a GitHub sign-in window.
#>
param(
    [string]$Zip = (Join-Path $PSScriptRoot "EnHi-LMP-JudgeBERT_code.zip"),
    [string]$RepoUrl = "https://github.com/udbhav968-creator/NLP_RESERACH_WORK.git"
)
$ErrorActionPreference = "Stop"
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw "Git is not installed. Install Git for Windows from https://git-scm.com/download/win and run again." }
$Dir = Join-Path $PSScriptRoot "EnHi-LMP-JudgeBERT"
if (-not (Test-Path (Join-Path $Dir ".git"))) {
    if (-not (Test-Path $Zip)) { throw "Zip not found: $Zip" }
    Expand-Archive -Path $Zip -DestinationPath $PSScriptRoot -Force
}
Set-Location $Dir
$prev = $ErrorActionPreference; $ErrorActionPreference = "Continue"
git remote remove origin 2>$null
$ErrorActionPreference = $prev
git remote add origin $RepoUrl
git branch -M main
git log --oneline
Write-Host "Pushing to $RepoUrl ..." -ForegroundColor Cyan
git push -u origin main
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Push was rejected. If the GitHub repository already has files (e.g. a README created on github.com), run:"
    Write-Host "    git pull origin main --allow-unrelated-histories --no-edit" -ForegroundColor Yellow
    Write-Host "    git push -u origin main" -ForegroundColor Yellow
    exit 1
}
Write-Host "Done: https://github.com/udbhav968-creator/NLP_RESERACH_WORK" -ForegroundColor Green
