"""Full training run: every experiment, every model, one command.

    python scripts/train_all.py                      # everything (GPU used automatically when present)
    python scripts/train_all.py --quick              # 2-epoch smoke test of the whole pipeline (~5 min)
    python scripts/train_all.py --skip-pretrained    # only E1-E5 + deployed model
    python scripts/train_all.py --resume             # skip steps this machine already finished (after a Colab disconnect)

Steps
  1. E1-E5 with the from-scratch models  (src/run_experiments.py: baselines, LegalDiff-GBR, ML-JudgeBERT, +LegalDiff)
  2. Hard cases and LaTeX tables          (src/select_cases.py, src/gen_tables.py)
  3. Pretrained encoders on the GPU       (src/finetune_pretrained.py: XLM-R, MuRIL, mBERT by default)
  4. Deployed model                       (api/lmp_service.py, web/export_model.py, node web/test.js, frontend/build.py)
  5. One comparison table                 (results/ALL_RESULTS.md and results/all_models.csv)
Every step's output is logged to results/logs/train_all_*.log.
"""
import argparse, csv, json, os, shutil, subprocess, sys, time
from pathlib import Path

R = Path(__file__).resolve().parent.parent
RES, LOGS = R / "results", R / "results" / "logs"
STATE = LOGS / "train_all_state.json"     # steps finished on THIS machine (not in git), used by --resume
PRETRAINED = ["xlm-roberta-base", "google/muril-base-cased", "bert-base-multilingual-cased"]
LR = {"xlm-roberta-base": "2e-5", "google/muril-base-cased": "3e-5", "bert-base-multilingual-cased": "3e-5"}


def gpu_name():
    try:
        import torch
        return torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
    except Exception:
        return None


def _state():
    try: return json.load(open(STATE))
    except Exception: return {}


def run(name, cmd, env=None, outputs=(), resume=False):
    st = _state()
    if resume and name in st and all((R / o).exists() for o in outputs):
        print(f"[skip] {name} (finished {st[name]})"); return True
    LOGS.mkdir(parents=True, exist_ok=True)
    log = LOGS / f"train_all_{name.replace(' ', '_').replace('/', '_')}.log"
    print(f"[run ] {name}: {' '.join(cmd)}", flush=True); t0 = time.time()
    with open(log, "w", encoding="utf-8") as fh:
        p = subprocess.Popen(cmd, cwd=R, env={**os.environ, **(env or {})}, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
        for line in p.stdout:
            fh.write(line)
            if any(k in line for k in ("fold ", "exp", "seed", "Error", "error", "best epoch")): print("       " + line.rstrip()[:160], flush=True)
        p.wait()
    ok = p.returncode == 0
    if ok:
        st = _state(); st[name] = time.strftime("%Y-%m-%d %H:%M"); json.dump(st, open(STATE, "w"), indent=1)
    print(f"[{'done' if ok else 'FAIL'}] {name} in {(time.time() - t0) / 60:.1f} min  (log: {log.relative_to(R)})", flush=True)
    return ok


def summary(models):
    rows = []
    e1 = json.load(open(RES / "exp1_summary.json"))
    for m, v in e1["overall"].items():
        a, bl, s = v["all"], e1["by_lang"][m], e1["sanity"][m]
        rows.append(dict(model=m, kind="from scratch / baseline", pearson=a["pearson"][0], spearman=a["spearman"][0], rmse=a["rmse"][0], mae=a["mae"][0],
                         f1_decision=a["f1_decision"][0], f1_not_preserved=a["f1_notpreserved"][0], r_en=bl["en"]["pearson"][0], r_hi=bl["hi"]["pearson"][0],
                         identical=s["identical_mean"], unrelated=s["unrelated_mean"]))
    for m in models:
        f = RES / f"pretrained_{m.replace('/', '_')}.json"
        if not f.exists(): continue
        for name, v in json.load(open(f)).items():
            rows.append(dict(model=name, kind="pretrained (GPU)", pearson=v["pearson"][0], spearman=v["spearman"][0], rmse=v["rmse"][0], mae=v["mae"][0],
                             f1_decision=v["f1_decision"][0], f1_not_preserved=v["f1_notpreserved"][0], r_en=v["pearson_en"], r_hi=v["pearson_hi"],
                             identical=v["identical_mean"], unrelated=v["unrelated_mean"]))
    rows.sort(key=lambda r: -r["pearson"])
    with open(RES / "all_models.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    e3 = json.load(open(RES / "exp3_domain.json")); e5 = json.load(open(RES / "exp5_explain.json"))
    md = ["# All results", "", f"5-fold cross-validation grouped by clause on {int(e1['overall']['LegalDiff-GBR']['all']['n'][0])} EnHi-LMP pairs (silver labels).", "",
          "| Model | Kind | r | ρ | RMSE | Not-preserved F1 | r EN | r HI | identical | unrelated |", "|---|---|---|---|---|---|---|---|---|---|"]
    md += [f"| {r['model']} | {r['kind']} | {r['pearson']:.3f} | {r['spearman']:.3f} | {r['rmse']:.2f} | {r['f1_not_preserved']:.2f} | {r['r_en']:.2f} | {r['r_hi']:.2f} | {r['identical']:.2f} | {r['unrelated']:.2f} |" for r in rows]
    fr = e3.get("EnHi->FrJUDGE (zero-shot)", {})
    md += ["", "Zero-shot on human-labelled FrJUDGE (Pearson r): " + ", ".join(f"{m} {v['pearson'][0]:.2f}" for m, v in fr.items()), "",
           f"Explanations (LegalDiff-GBR): error-detection F1 {e5['binary']['f1']:.2f}, exact type {100 * e5['type_acc_on_errors']:.0f}%, macro-F1 {e5['macro_f1']:.2f}.", ""]
    (RES / "ALL_RESULTS.md").write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true", help="2 epochs, 1 seed, 2 folds for pretrained models: checks the pipeline end to end")
    ap.add_argument("--resume", action="store_true", help="skip steps whose outputs already exist")
    ap.add_argument("--skip-experiments", action="store_true"); ap.add_argument("--skip-pretrained", action="store_true")
    ap.add_argument("--models", nargs="+", default=PRETRAINED, help="Hugging Face encoders to fine-tune")
    ap.add_argument("--epochs", type=int, default=8, help="epochs for pretrained encoders")
    a = ap.parse_args()

    g = gpu_name(); cores = os.cpu_count() or 2
    print(f"GPU: {g or 'none (CPU only)'} · CPU cores: {cores} · quick={a.quick}", flush=True)
    env = {"THREADS": str(cores), "PYTHONIOENCODING": "utf-8"}
    if a.quick: env["EPOCHS"] = "2"
    t0 = time.time(); failed = []
    backup = None
    if a.quick:   # a smoke test must never overwrite the real results: snapshot results/ and restore it at the end
        backup = Path(os.environ.get("TMPDIR", "/tmp")) / f"lmp_results_backup_{int(t0)}"
        shutil.copytree(RES, backup)
        if STATE.exists(): STATE.unlink()
        print(f"quick mode: results/ backed up to {backup} and restored at the end", flush=True)

    if not a.skip_experiments:
        steps = [("E1 E4 baselines and models", ["exp1"], ["results/exp1_summary.json"]), ("E2 cross-lingual", ["exp2"], ["results/exp2_crosslingual.json"]),
                 ("E3 domain and FrJUDGE", ["exp3"], ["results/exp3_domain.json"]), ("E5 explanations", ["exp5"], ["results/exp5_explain.json"])]
        for name, arg, outs in steps:
            if not run(name, [sys.executable, "src/run_experiments.py", *arg], env, outs, a.resume): failed.append(name)
        run("hard cases", [sys.executable, "src/select_cases.py"], env)
        run("latex tables", [sys.executable, "src/gen_tables.py"], env)

    if not a.skip_pretrained:
        if not g: print("[warn] no GPU: pretrained encoders will be very slow on CPU. In Colab: Runtime > Change runtime type > T4 GPU.")
        for m in a.models:
            out = f"results/pretrained_{m.replace('/', '_')}.json"
            cmd = [sys.executable, "src/finetune_pretrained.py", "--model", m, "--epochs", str(2 if a.quick else a.epochs), "--lr", LR.get(m, "2e-5")]
            if a.quick: cmd += ["--seeds", "0", "--limit_folds", "2"]
            if not run(f"pretrained {m}", cmd, env, [out], a.resume): failed.append(m)

    run("deployed model", [sys.executable, "api/lmp_service.py"], env)
    run("web model export", [sys.executable, "web/export_model.py"], env)
    if shutil.which("node"): run("JS parity test", ["node", "web/test.js"], env)
    run("web app build", [sys.executable, "frontend/build.py"], env)
    try:
        summary(a.models)
    finally:
        if backup:
            shutil.rmtree(RES); shutil.copytree(backup, RES)
            print("quick mode: the numbers above are a smoke test; the real results/ folder has been restored.")
    print(f"\nTotal time {(time.time() - t0) / 60:.1f} min. Failed steps: {failed or 'none'}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
