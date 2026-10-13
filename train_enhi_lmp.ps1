<#
.SYNOPSIS
    Train and evaluate the EnHi-LMP / ML-JudgeBERT project end to end on Windows (PowerShell 5.1 or 7+).

.DESCRIPTION
    1. Unzips the project (if needed) and creates a Python virtual environment (.venv).
    2. Installs PyTorch (CUDA build if an NVIDIA GPU is found, CPU build otherwise) and all requirements.
    3. Optional: merges two human annotation workbooks and switches all experiments to the human labels.
    4. Runs the CPU experiments E1-E5 (baselines, LegalDiff-GBR, ML-JudgeBERT from scratch, transfer, sanity, explanations).
    5. Fine-tunes pretrained multilingual encoders (XLM-R base, MuRIL base) with the same protocol.
    6. Prints a results summary. Every step is logged to results\logs\.

.EXAMPLE
    # one-time, in this PowerShell window only:
    Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
    # everything (put this script next to EnHi-LMP-JudgeBERT_code.zip):
    .\train_enhi_lmp.ps1

.EXAMPLE
    .\train_enhi_lmp.ps1 -Stage pretrained                       # only XLM-R + MuRIL
    .\train_enhi_lmp.ps1 -Stage cpu                              # only experiments E1-E5
    .\train_enhi_lmp.ps1 -Models xlm-roberta-base -Epochs 6      # one encoder, 6 epochs
    .\train_enhi_lmp.ps1 -HumanA .\ann_A.xlsx -HumanB .\ann_B.xlsx   # use human labels

.NOTES
    Time on a typical laptop CPU: setup 5-10 min, E1-E5 about 60-90 min.
    Pretrained fine-tuning: about 10-20 min per model on an NVIDIA GPU; many hours on CPU, so on CPU the script
    runs a 1-fold, 1-seed smoke test unless -AllowCpuFinetune is given.
#>
[CmdletBinding()]
param(
    [string]$Zip = (Join-Path $PSScriptRoot "EnHi-LMP-JudgeBERT_code.zip"),
    [string]$WorkDir = $PSScriptRoot,
    [ValidateSet("all", "setup", "cpu", "pretrained", "summary")]
    [string]$Stage = "all",
    [string[]]$Models = @("xlm-roberta-base", "google/muril-base-cased"),
    [int]$Epochs = 5,
    [int]$BatchSize = 16,
    [double]$LearningRate = 2e-5,
    [int[]]$Seeds = @(0, 1, 2),
    [string]$HumanA = "",
    [string]$HumanB = "",
    [switch]$CpuOnly,
    [switch]$AllowCpuFinetune
)

$ErrorActionPreference = "Stop"
$Start = Get-Date

function Write-Step([string]$Message) {
    Write-Host ""
    Write-Host ("=" * 78) -ForegroundColor DarkCyan
    Write-Host ("[{0:HH:mm:ss}] {1}" -f (Get-Date), $Message) -ForegroundColor Cyan
    Write-Host ("=" * 78) -ForegroundColor DarkCyan
}

function Invoke-Native {
    # Runs an external program, streams + logs its output, and stops the script if it fails.
    param([string]$Exe, [string[]]$Arguments, [string]$LogName)
    $log = Join-Path $script:LogDir $LogName
    $previous = $ErrorActionPreference
    $ErrorActionPreference = "Continue"          # stderr warnings must not abort Windows PowerShell 5.1
    & $Exe @Arguments 2>&1 | ForEach-Object { "$_" } | Tee-Object -FilePath $log
    $code = $LASTEXITCODE
    $ErrorActionPreference = $previous
    if ($code -ne 0) { throw "Step '$LogName' failed with exit code $code. Full output: $log" }
}

function Find-Python {
    # Prefer the Windows 'py' launcher with a version PyTorch supports, then plain 'python'.
    $candidates = @()
    if (Get-Command py -ErrorAction SilentlyContinue) {
        foreach ($v in "3.12", "3.11", "3.10") { $candidates += , @("py", "-$v") }
    }
    foreach ($name in "python", "python3") {
        if (Get-Command $name -ErrorAction SilentlyContinue) { $candidates += , @($name) }
    }
    foreach ($c in $candidates) {
        $exe = $c[0]; $pre = @(); if ($c.Count -gt 1) { $pre = $c[1..($c.Count - 1)] }
        $previous = $ErrorActionPreference; $ErrorActionPreference = "Continue"
        $ver = & $exe @pre -c "import sys; print('%d.%d' % sys.version_info[:2])" 2>$null
        $ErrorActionPreference = $previous
        if ($LASTEXITCODE -eq 0 -and $ver) {
            $parts = "$ver".Trim().Split(".")
            $major = [int]$parts[0]; $minor = [int]$parts[1]
            if ($major -eq 3 -and $minor -ge 10 -and $minor -le 13) { return ,(@($exe) + $pre) }
        }
    }
    throw "Python 3.10-3.13 not found. Install Python 3.12 from https://www.python.org/downloads/ (tick 'Add python.exe to PATH') and run again."
}

# ------------------------------------------------------------------ 1. project folder
Write-Step "1/6  Locating the project"
$Repo = Join-Path $WorkDir "EnHi-LMP-JudgeBERT"
if (-not (Test-Path (Join-Path $Repo "src\run_experiments.py"))) {
    if (Test-Path (Join-Path $WorkDir "src\run_experiments.py")) {
        $Repo = $WorkDir                                     # script placed inside the project folder
    } elseif (Test-Path $Zip) {
        Write-Host "Unzipping $Zip ..."
        Expand-Archive -Path $Zip -DestinationPath $WorkDir -Force
    } else {
        throw "Project not found. Put this script next to EnHi-LMP-JudgeBERT_code.zip (or pass -Zip <path>)."
    }
}
$Repo = (Resolve-Path $Repo).Path
$script:LogDir = Join-Path $Repo "results\logs"
New-Item -ItemType Directory -Force -Path $script:LogDir | Out-Null
Set-Location $Repo
$Src = Join-Path $Repo "src"
Write-Host "Project folder: $Repo"

# ------------------------------------------------------------------ 2. Python environment
$VenvDir = Join-Path $Repo ".venv"
$Py = Join-Path $VenvDir "Scripts\python.exe"
if (-not (Test-Path $Py)) { $Py = Join-Path $VenvDir "bin/python" }    # non-Windows PowerShell

$env:PYTHONUTF8 = "1"                       # Hindi text: always read/write UTF-8
$env:PYTHONIOENCODING = "utf-8"
$env:THREADS = [string][Environment]::ProcessorCount
$env:HF_HUB_DISABLE_SYMLINKS_WARNING = "1"
$env:TOKENIZERS_PARALLELISM = "false"
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }

$HasGpu = (-not $CpuOnly) -and [bool](Get-Command nvidia-smi -ErrorAction SilentlyContinue)

if ($Stage -in @("all", "setup") -or -not (Test-Path $Py)) {
    Write-Step "2/6  Creating the virtual environment and installing packages"
    if (-not (Test-Path $Py)) {
        $sysPy = Find-Python
        $exe = $sysPy[0]; $pre = @(); if ($sysPy.Count -gt 1) { $pre = $sysPy[1..($sysPy.Count - 1)] }
        Write-Host "Using: $($sysPy -join ' ')"
        Invoke-Native $exe ($pre + @("-m", "venv", $VenvDir)) "00_venv.log"
        $Py = Join-Path $VenvDir "Scripts\python.exe"
        if (-not (Test-Path $Py)) { $Py = Join-Path $VenvDir "bin/python" }
    }
    Invoke-Native $Py @("-m", "pip", "install", "--upgrade", "pip", "wheel") "01_pip_upgrade.log"
    if ($HasGpu) {
        Write-Host "NVIDIA GPU found -> installing a CUDA build of PyTorch" -ForegroundColor Green
        $installed = $false
        foreach ($cu in "cu126", "cu124", "cu121") {
            try {
                Invoke-Native $Py @("-m", "pip", "install", "torch", "--index-url", "https://download.pytorch.org/whl/$cu") "02_torch_$cu.log"
                $installed = $true; break
            } catch { Write-Warning "PyTorch $cu build not available for this Python, trying the next one..." }
        }
        if (-not $installed) { Invoke-Native $Py @("-m", "pip", "install", "torch") "02_torch_pypi.log" }
    } else {
        Write-Host "No NVIDIA GPU (or -CpuOnly) -> installing the CPU build of PyTorch" -ForegroundColor Yellow
        Invoke-Native $Py @("-m", "pip", "install", "torch", "--index-url", "https://download.pytorch.org/whl/cpu") "02_torch.log"
    }
    Invoke-Native $Py @("-m", "pip", "install", "-r", "requirements.txt", "transformers>=4.40", "accelerate", "sentencepiece", "protobuf") "03_requirements.log"
}

Write-Step "3/6  Checking the environment"
Invoke-Native $Py @("-c", "import torch, transformers, sklearn, sacrebleu, wordllama; print('torch', torch.__version__, '| CUDA available:', torch.cuda.is_available(), '| GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'none'); print('transformers', transformers.__version__)") "04_check.log"
$CudaOk = ((& $Py -c "import torch; print(torch.cuda.is_available())") | Select-Object -Last 1).Trim() -eq "True"

# ------------------------------------------------------------------ 3. labels (silver or human)
$env:LMP_DATA = "enhi_lmp.jsonl"
if ($HumanA -and $HumanB) {
    Write-Step "     Merging human annotations (Krippendorff's alpha, adjudication list)"
    $a = (Resolve-Path $HumanA).Path; $b = (Resolve-Path $HumanB).Path
    Invoke-Native $Py @((Join-Path $Src "merge_annotations.py"), $a, $b) "05_merge_annotations.log"
    $env:LMP_DATA = "enhi_lmp_human.jsonl"
    Write-Host "All experiments below use HUMAN labels (data\enhi_lmp_human.jsonl)." -ForegroundColor Green
} elseif ($HumanA -or $HumanB) {
    throw "Give both -HumanA and -HumanB (one workbook per annotator)."
} else {
    Write-Host "Using rubric-based silver labels (data\enhi_lmp.jsonl). Pass -HumanA/-HumanB after annotation." -ForegroundColor Yellow
}

# ------------------------------------------------------------------ 4. CPU experiments E1-E5
if ($Stage -in @("all", "cpu")) {
    Write-Step "4/6  Experiments E1-E5 (baselines, LegalDiff, ML-JudgeBERT from scratch) - about 60-90 min on CPU"
    Invoke-Native $Py @((Join-Path $Src "run_experiments.py"), "exp1") "10_exp1_E1_E4.log"      # E1 + E4 sanity + predictions for E5
    Invoke-Native $Py @((Join-Path $Src "run_experiments.py"), "exp2") "11_exp2_crosslingual.log"
    Invoke-Native $Py @((Join-Path $Src "run_experiments.py"), "exp3") "12_exp3_domain_frjudge.log"
    Invoke-Native $Py @((Join-Path $Src "run_experiments.py"), "exp5") "13_exp5_explanations.log"
    Invoke-Native $Py @((Join-Path $Src "select_cases.py")) "14_hard_cases.log"
    Invoke-Native $Py @((Join-Path $Src "gen_tables.py")) "15_latex_tables.log"
}

# ------------------------------------------------------------------ 5. pretrained encoders
if ($Stage -in @("all", "pretrained")) {
    Write-Step "5/6  Fine-tuning pretrained encoders: $($Models -join ', ')"
    $extra = @()
    if (-not $CudaOk) {
        if ($AllowCpuFinetune) {
            Write-Warning "No CUDA GPU: full fine-tuning on CPU can take many hours per model."
        } else {
            Write-Warning "No CUDA GPU: running a 1-fold, 1-seed SMOKE TEST only. Use Google Colab (T4) or pass -AllowCpuFinetune for the full run."
            $extra = @("--limit_folds", "1")
            $Seeds = @(0)
        }
    }
    foreach ($m in $Models) {
        $tag = $m -replace "[/\\:]", "_"
        $ftArgs = @((Join-Path $Src "finetune_pretrained.py"), "--model", $m, "--epochs", "$Epochs", "--bs", "$BatchSize",
                  "--lr", ([string]::Format([Globalization.CultureInfo]::InvariantCulture, "{0}", $LearningRate)),
                  "--seeds") + ($Seeds | ForEach-Object { "$_" }) + $extra
        Invoke-Native $Py $ftArgs "20_pretrained_$tag.log"
    }
}

# ------------------------------------------------------------------ 6. summary
Write-Step "6/6  Results summary"
$summary = @'
import json, glob, os
rows = []
p = 'results/exp1_summary.json'
if os.path.exists(p):
    for m, v in json.load(open(p, encoding='utf-8'))['overall'].items():
        a = v['all']; rows.append((m + ' [CPU, E1]', a['pearson'][0], a['spearman'][0], a['rmse'][0], a['mae'][0]))
for f in sorted(glob.glob('results/pretrained_*.json')):
    for m, v in json.load(open(f, encoding='utf-8')).items():
        rows.append((m + ' [pretrained]', v['pearson'][0], v['spearman'][0], v['rmse'][0], v['mae'][0]))
print(f"{'System':62s} {'r':>6s} {'rho':>6s} {'RMSE':>6s} {'MAE':>6s}")
print('-' * 90)
for name, r, rho, rmse, mae in sorted(rows, key=lambda x: -x[1]):
    print(f'{name:62s} {r:6.3f} {rho:6.3f} {rmse:6.2f} {mae:6.2f}')
e = 'results/exp5_explain.json'
if os.path.exists(e):
    d = json.load(open(e, encoding='utf-8'))
    print(f"\nExplanations: error-detection F1 {d['binary']['f1']:.2f} | exact type correct {100*d['type_acc_on_errors']:.0f}% | macro-F1 {d['macro_f1']:.2f}")
print('\nLabels used:', os.environ.get('LMP_DATA'))
'@
$summaryFile = Join-Path $script:LogDir "summary.py"
Set-Content -Path $summaryFile -Value $summary -Encoding UTF8
Invoke-Native $Py @($summaryFile) "99_summary.log"

$elapsed = (Get-Date) - $Start
Write-Host ""
Write-Host ("Done in {0:hh\:mm\:ss}. Results: {1}  |  Logs: {2}" -f $elapsed, (Join-Path $Repo "results"), $script:LogDir) -ForegroundColor Green
