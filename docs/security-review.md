# Security review — claims-skill-loop

**Owner:** A1 (design-time review, Phase 1). **Date:** 2026-09-06. **Sign-off:** L0 in Phase 5 after running the checks below. Status values: `design` (requirement stated, implementation pending) · `implemented` (code exists, not yet verified) · `verified` (check run and recorded in `docs/verification-log.md`). **Nothing below is marked `verified` yet.**

## 1. Threat model in one paragraph

The system runs locally on the author's machine, offline after a one-time dataset download. Untrusted inputs are: dataset text (synthetic but arbitrary strings), operator response files (written by a model), and skill files (model-authored Markdown). Assets to protect: the author's Claude Code session and any credentials on the machine, the integrity of the frozen evaluation (goldens, rubric, data), and the filesystem outside the run's output directories. The main risks are credential misuse, prompt injection reaching a decision, and model output reaching code execution.

## 2. Requirements, mechanisms, and checks

| # | Requirement | Mechanism | Owner | Phase 5 check | Status |
|---|---|---|---|---|---|
| S1 | **Synthetic data only; no PHI** | Only `xpertsystems/hlt008-sample` (synthetic) is used; `data/README.md` states it; no other data source may be added without asking the user; no free-text dataset fields are copied into logs, requests, or reports beyond ≤ 50-char samples | A2 | `data/README.md` present; `grep -rn "sample_values" data/processed/manifest.json` shows truncated values | design |
| S2 | **Licence and attribution (CC-BY-NC-4.0)** | Attribution + licence in `data/README.md`, `README.md`, and the write-up; non-commercial educational use; raw CSVs git-ignored and re-downloaded by script, never redistributed | A2, A1 | `grep -n "CC-BY-NC" README.md data/README.md docs/writeup.md` | design |
| S3 | **No secrets in source control or logs** | `.env` git-ignored; `.env.example` has empty values only; loggers write only whitelisted fields (never `os.environ`); `verify.sh` greps `src/ logs/ artifacts/ docs/` for key-like patterns (`sk-ant-`, `ANTHROPIC_API_KEY=` with a value) | L0, A5 | `git check-ignore .env`; `verify.sh` secret scan reports zero hits | design |
| S4 | **No credential reuse of any kind** | The runtime never reads Claude Code session state (`~/.claude`, OAuth tokens, cookies, keychain), never spawns the CLI, never uses the Agent SDK, never bridges to a headless CLI, and needs no API key in `manual`/`stub` modes. The operator is a subagent spawned by the lead **inside** the session and talks to the runtime only via JSON files | L0 | `grep -rn -E "claude|oauth|keychain|\.claude/|subprocess" src/` returns only the string `claude-fable-5-1` / `claude-code-subagent` identifiers and no CLI invocation | design |
| S5 | **API key separation and fail-closed live mode** | `anthropic_api` mode instantiates `ChatAnthropic` only when `CLAIMS_SKILL_LOOP_LLM_MODE=anthropic_api` **and** `ANTHROPIC_API_KEY` is set; otherwise raises a clear error before any graph work; `langchain_anthropic` imported only inside that branch; not used in this study | L0 | `tests/test_llm_provider.py` fail-closed case | design |
| S6 | **Operator files are JSON only and validated** | Request/response files live only under `artifacts/manual/<run_id>/<condition>/`; `resume` accepts only a `.response.json` path under that directory, ≤ 256 KB, parsed with `json.loads` (no YAML, no pickle); response validated against the pydantic response model (`extra="forbid"`, bounded string lengths, enumerated component ids and options); failures logged as `operator_validation_error` and re-requested (≤ 2), never hand-edited | L0 | `tests/test_llm_provider.py` rejects oversized, mis-located, non-JSON, and extra-field responses | design |
| S7 | **Prompt-injection hygiene** | Dataset text reaches operator requests only as `sample_values` truncated to 50 chars and as column/table identifiers; skills reach requests only after passing the validator's safety checks; the operator can only choose catalogue ids and options, so injected instructions cannot become code or file operations; free-text fields (`rationale`, lessons, skill sections) are bounded and never executed or interpolated into commands | A2, A4, L0 | manifest sample length test (A2); validator safety tests (A4); request builder test that no raw dataset rows appear (L0) | design |
| S8 | **Restricted execution — no model-generated code** | `task_runner.execute` interprets a structured plan against a fixed component catalogue; no `eval`, `exec`, `compile`, `subprocess`, `os.system`, shell, `importlib` of plan-supplied names, or network; unknown components/params become structured errors | A6 | `grep -n -E "\b(eval|exec|compile|subprocess|os\.system|popen)\(" src/task_runner.py src/analyses/*.py` returns nothing; `tests/test_task_runner.py` | design |
| S9 | **Output-directory confinement** | Every write resolves the target path and asserts it is inside `run_context.output_dir` (`Path.resolve()` + `relative_to`); artifact names come from the catalogue, not from the plan's free text; matplotlib Agg backend, no `savefig` outside the directory | A6 | `tests/test_task_runner.py` path-escape case (`../`) is rejected | design |
| S10 | **Per-attempt timeouts** | `execution_timeout_seconds` (`config/graph.yaml`, default 300) enforced cooperatively between components; on expiry the executor returns `status: partial` with an `errors` entry of type `timeout`; operator waits have no timeout by design (human/agent-in-the-loop) but are visible in `experiment_status.json` (`waiting_since`) | A6, L0 | `tests/test_task_runner.py` timeout case with a tiny deadline | design |
| S11 | **No network after the one-time download** | Only `src/download_data.py` imports `huggingface_hub`; no `requests`/`urllib`/`http.client`/sockets elsewhere in `src/`; tests never touch the network; dashboard HTML has no external assets; charts use Agg | A2, A5, A6, L0 | `grep -rn -E "huggingface_hub|requests|urllib|http\.client|socket" src/ | grep -v download_data.py` returns nothing | design |
| S12 | **Skills cannot instruct code execution** | Skills are Markdown shown to the operator as text; the validator rejects proposals containing shell, network, credential, or code-execution instructions; foundational skills are reviewed by the lead | A4 | validator safety tests; `grep -rn -E "subprocess|curl|wget|api[_ ]key|token" skills/` returns nothing actionable | design |
| S13 | **Log and state hygiene** | Graph state, checkpoints, and logs contain plans, evaluations, bounded operator text, paths, and hashes — never secrets, raw dataset rows, or unbounded prompts; `logs/checkpoints/*.sqlite` should be git-ignored (request to L0, see §4) | A5, L0 | `validate_logs()`; `.gitignore` includes checkpoints | design |
| S14 | **Frozen-evaluation integrity** | `config/freeze_manifest.json` hashes tasks, rubric, goldens, and raw data; `init` (manual mode) refuses on drift; every evaluation event carries `freeze_sha256`; goldens built by independent code | L0, A3 | `init` with a modified golden aborts (manual test recorded) | design |
| S15 | **Dependency integrity** | `uv.lock` pins the full resolution; no installs at run time; optional `anthropic` extra not installed for the study | L0 | `uv sync --extra dev --frozen` succeeds | design |
| S16 | **Least-privilege agents** | Subagent definitions restrict tools: `experiment-operator` Read/Write only; A1 no implementation code; only A2 may use the network and only for the download | L0 | `.claude/agents/*.md` `tools:` lines | implemented |

## 3. Explicitly prohibited

- Extracting, reusing, proxying, or exposing Claude Code session credentials, browser cookies, OAuth tokens, or subscription state for the Python runtime.
- Any Agent SDK integration or headless-CLI bridge that would turn the Claude Code session into a hidden API backend.
- Executing model-generated code, shell commands, or file operations named in operator responses or skills.
- Network access from any module other than `src/download_data.py`.
- Adding a data source, or presenting results as medical, actuarial, fraud, underwriting, pricing, adjudication, legal, regulatory, or operational evidence.

## 4. Requests to other owners

- **L0:** add `logs/checkpoints/*.sqlite` and `artifacts/manual/**/*.tmp` to `.gitignore`; include the S3/S4/S8/S11 greps in `scripts/verify.sh`.
- **A5:** `validate_logs()` should flag any record containing `ANTHROPIC_API_KEY` or a `sk-ant-` prefix.
- **A6:** expose `timeout_seconds` in `run_context` (plan §13) and document the cooperative deadline in `tests/test_task_runner.py`.

## 5. Phase 5 verification checklist (to be run by L0 and appended to `docs/verification-log.md`)

```bash
git check-ignore .env logs/checkpoints/run_001.sqlite
grep -rn -E "sk-ant-|ANTHROPIC_API_KEY=[^\s]" src/ logs/ artifacts/ docs/ config/ || echo "no key material"
grep -rn -E "huggingface_hub|requests|urllib|http\.client|socket" src/ | grep -v download_data.py || echo "no network imports outside download_data"
grep -rn -E "\b(eval|exec|compile|subprocess|os\.system|popen)\(" src/task_runner.py src/analyses/ || echo "no dynamic execution in executor"
uv run --extra dev pytest tests/test_llm_provider.py tests/test_task_runner.py tests/test_skill_store.py -q
```
