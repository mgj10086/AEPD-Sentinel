#!/usr/bin/env python3
"""
LoopCode LRS Validator — Granular, traceable scoring.
Every single point is attributable to a specific sub-criterion.

Score = Σ (dimension_score × weight)  across 7 dimensions
Each dimension: 0–100 pts, decomposed into explicit sub-items.

Run: python3 .loopcode/validate.py
     python3 .loopcode/validate.py --verbose   (show per-point breakdown)
"""

import os
import re
import sys
import yaml

# ── Dimension definitions ─────────────────────────────────────
# Each dimension: weight, max 100 pts, composed of sub-items.
# Each sub-item: (label, earned, max_points)
# earned is a lambda: (config, loops_dir) -> bool | int

def _agent_count(config: dict) -> int:
    """Count total agents across all pipeline steps."""
    n = 0
    for step in config.get("pipeline", []):
        if "parallel" in step:
            n += len(step["parallel"])
        elif "agents" in step:
            n += len(step["agents"])
        elif "prompt" in step:
            n += 1
    return n

def _checker_has_human_role(config: dict) -> bool:
    """Check if checker name implies a human-in-the-loop role."""
    verify = config.get("verify") or {}
    checkers = verify.get("checker", "")
    if isinstance(checkers, list):
        checkers = " ".join(checkers)
    return bool(re.search(
        r"Expert|Auditor|Verifier|Reviewer|Associate|Inspector|Monitor|Specialist",
        checkers, re.IGNORECASE
    ))

def _description_has_metrics(config: dict) -> int:
    """Count structured enumeration indicators in description."""
    desc = config.get("description", "")
    score = 0
    # Semicolons separating items
    if desc.count(";") >= 2:
        score += 8
    # Numbered items (1. 2. or 1) 2))
    if re.search(r"\d[\.\)]\s", desc):
        score += 7
    # Colon-separated list with ≥3 commas
    if ":" in desc and desc.count(",") >= 3:
        score += 8
    return min(score, 15)

def _desc_has_quality_statement(config: dict) -> int:
    """Check for quality/success-criteria language in description."""
    desc = config.get("description", "")
    keywords = [
        "ensure", "ensures", "quality", "compliance", "accurate",
        "comprehensive", "complete", "regulatory", "standard",
        "actionable", "clinically meaningful", "statistically sound"
    ]
    found = sum(1 for kw in keywords if kw.lower() in desc.lower())
    if found >= 4: return 15
    if found >= 2: return 10
    if found >= 1: return 5
    return 0

# ── Granular rubric (100 pts per dimension) ───────────────────

DIMENSIONS = [
    {
        "key": "quantifiable_goal",
        "weight": 0.20,
        "label": "目标可量化",
        "items": [
            # (label,                    earned_fn,                        max_pts)
            ("kebab-case 命名",           lambda c,_: "-" in c.get("name",""),           10),
            ("名称 ≥ 10 字符",           lambda c,_: len(c.get("name","")) >= 10,       10),
            ("名称含业务动词",            lambda c,_: bool(re.search(
                r"review|audit|detect|verify|check|mine|triage|coding|report|signal",
                c.get("name",""), re.I)),                                            10),
            ("description 字段存在",      lambda c,_: len(c.get("description","")) > 0,  10),
            ("description ≥ 80 字符",    lambda c,_: len(c.get("description","")) >= 80, 15),
            ("描述含结构化列举",          lambda c,_: _description_has_metrics(c) > 0,    15),
            ("描述含成功标准/质量声明",   lambda c,_: _desc_has_quality_statement(c) > 0, 15),
            ("trigger.description ≥ 20", lambda c,_: len(
                (c.get("trigger") or {}).get("description","")) >= 20,                 15),
        ],
    },
    {
        "key": "termination_condition",
        "weight": 0.20,
        "label": "终止条件",
        "items": [
            ("maxIterations 已设置",       lambda c,_: "maxIterations" in (c.get("budget") or {}),      25),
            ("maxIterations ≤ 10",         lambda c,_: (c.get("budget") or {}).get("maxIterations",99) <= 10, 10),
            ("maxDurationMinutes 已设置",  lambda c,_: "maxDurationMinutes" in (c.get("budget") or {}), 25),
            ("maxDurationMinutes ≤ 30",    lambda c,_: (c.get("budget") or {}).get("maxDurationMinutes",99) <= 30, 10),
            ("maxTokens 已设置",           lambda c,_: "maxTokens" in (c.get("budget") or {}),          20),
            ("maxTokens ≤ 500K",           lambda c,_: (c.get("budget") or {}).get("maxTokens",10**9) <= 500000, 10),
        ],
    },
    {
        "key": "verification",
        "weight": 0.15,
        "label": "验证机制",
        "items": [
            ("verify 配置存在",           lambda c,_: c.get("verify") is not None,                    15),
            ("maker 非空",               lambda c,_: bool((c.get("verify") or {}).get("maker")),      20),
            ("checker 非空",             lambda c,_: bool((c.get("verify") or {}).get("checker")),    20),
            ("Maker ≠ Checker 无交集",   lambda c,_: _maker_checker_separated(c),                     25),
            ("maxRounds 显式设置",       lambda c,_: "maxRounds" in (c.get("verify") or {}),          10),
            ("maxRounds ≥ 2",            lambda c,_: (c.get("verify") or {}).get("maxRounds",0) >= 2, 10),
        ],
    },
    {
        "key": "failure_recovery",
        "weight": 0.15,
        "label": "失败恢复",
        "items": [
            ("autoRetry 显式声明",       lambda c,_: "autoRetry" in (c.get("verify") or {}),         10),
            ("autoRetry = true",         lambda c,_: (c.get("verify") or {}).get("autoRetry") is True, 25),
            ("maxRounds ≥ 2 (允许多轮)", lambda c,_: (c.get("verify") or {}).get("maxRounds",0) >= 2, 20),
            ("maxRounds ≥ 3 (充足修正)", lambda c,_: (c.get("verify") or {}).get("maxRounds",0) >= 3, 15),
            ("maxRounds ≥ 5 (深度修正)", lambda c,_: (c.get("verify") or {}).get("maxRounds",0) >= 5, 10),
            ("并行 agent ≥ 2 (故障隔离)", lambda c,_: _agent_count(c) >= 2,                           10),
            ("并行 agent ≥ 3 (冗余容错)", lambda c,_: _agent_count(c) >= 3,                           10),
        ],
    },
    {
        "key": "budget_control",
        "weight": 0.10,
        "label": "预算控制",
        "items": [
            ("maxTokens 已设置",          lambda c,_: "maxTokens" in (c.get("budget") or {}),          25),
            ("maxDurationMinutes 已设置", lambda c,_: "maxDurationMinutes" in (c.get("budget") or {}), 20),
            ("maxIterations 已设置",      lambda c,_: "maxIterations" in (c.get("budget") or {}),      20),
            ("maxCostUsd 已设置",         lambda c,_: "maxCostUsd" in (c.get("budget") or {}),         20),
            ("≥3 项预算控制",             lambda c,_: _budget_item_count(c) >= 3,                      10),
            ("全部 4 项预算控制",          lambda c,_: _budget_item_count(c) >= 4,                      5),
        ],
    },
    {
        "key": "human_intervention",
        "weight": 0.10,
        "label": "人工介入",
        "items": [
            ("maxRounds 已设置",          lambda c,_: "maxRounds" in (c.get("verify") or {}),         15),
            ("maxRounds ≥ 2 (有审查机会)", lambda c,_: (c.get("verify") or {}).get("maxRounds",0) >= 2, 15),
            ("maxRounds ≥ 3 (多轮后升级)", lambda c,_: (c.get("verify") or {}).get("maxRounds",0) >= 3, 20),
            ("maxRounds ≥ 5 (强制多轮复核)", lambda c,_: (c.get("verify") or {}).get("maxRounds",0) >= 5, 10),
            ("checker 含人工角色词",       lambda c,_: _checker_has_human_role(c),                     20),
            ("pipeline agent ≥ 2 (多人裁决)", lambda c,_: _agent_count(c) >= 2,                        20),
        ],
    },
    {
        "key": "state_persistence",
        "weight": 0.10,
        "label": "状态持久化",
        "items": [
            ("memory 配置存在",           lambda c,_: c.get("memory") is not None,                    20),
            ("memory.store 明确指定",     lambda c,_: bool((c.get("memory") or {}).get("store")),      20),
            ("memory.path 明确指定",      lambda c,_: bool((c.get("memory") or {}).get("path")),       20),
            ("store = filesystem",        lambda c,_: (c.get("memory") or {}).get("store") == "filesystem", 20),
            (".loopcode/state/ 目录存在", lambda c,ld: os.path.isdir(
                os.path.join(ld, (c.get("memory") or {}).get("path", ".loopcode/state"))),            20),
        ],
    },
]

# ── Helper functions ──────────────────────────────────────────

def _maker_checker_separated(config: dict) -> bool:
    v = config.get("verify") or {}
    makers = v.get("maker", [])
    checkers = v.get("checker", [])
    if isinstance(makers, str): makers = [makers]
    if isinstance(checkers, str): checkers = [checkers]
    if not makers or not checkers:
        return False
    return not any(m in checkers for m in makers)

def _budget_item_count(config: dict) -> int:
    b = config.get("budget") or {}
    return sum(1 for k in ["maxTokens","maxDurationMinutes","maxIterations","maxCostUsd"] if k in b)

def _earned(val) -> int:
    """Evaluate a sub-item: bool -> max or 0; int -> direct value."""
    if isinstance(val, bool):
        return 0  # placeholder — actual eval happens with max_pts
    if isinstance(val, int):
        return val
    return 0

def score_to_grade(s: int) -> str:
    if s >= 90: return "A"
    if s >= 80: return "B"
    if s >= 65: return "C"
    if s >= 50: return "D"
    return "F"

# ── LRS Calculator ─────────────────────────────────────────────

def calculate_lrs(config: dict, project_dir: str, verbose: bool = False) -> dict:
    """
    Returns { total, dimensions: {key: score}, items: {key: [(label, earned, max), ...]}, issues, strengths }
    """
    dim_scores = {}
    all_items = {}
    issues = []
    strengths = []

    for dim in DIMENSIONS:
        key = dim["key"]
        items = dim["items"]
        item_results = []
        dim_total = 0

        for label, fn, max_pts in items:
            try:
                result = fn(config, project_dir)
            except Exception:
                result = False

            if isinstance(result, bool):
                earned = max_pts if result else 0
            elif isinstance(result, (int, float)):
                earned = min(int(result), max_pts)
            else:
                earned = 0

            item_results.append((label, earned, max_pts))
            dim_total += earned

        # Clamp to 100
        dim_total = min(dim_total, 100)
        dim_scores[key] = dim_total
        all_items[key] = item_results

        # Auto-generate issues/strengths based on missed items
        missed_all = [(lbl, earned, max_pts) for lbl, earned, max_pts in item_results if earned < max_pts]
        missed_high = [(lbl, earned, max_pts) for lbl, earned, max_pts in missed_all if max_pts >= 15]
        zero_high = [(lbl, earned, max_pts) for lbl, earned, max_pts in missed_high if earned == 0]

        if dim_total == 100:
            strengths.append(f"{dim['label']}: 满分通过 ({len(item_results)}/{len(item_results)} 项)")
        elif dim_total >= 80:
            if missed_high:
                names = ", ".join(lbl for lbl, _, _ in missed_high[:2])
                strengths.append(f"{dim['label']}: {dim_total}/100 — 可提升: {names}")
            else:
                strengths.append(f"{dim['label']}: {dim_total}/100")
        elif dim_total >= 50:
            if zero_high:
                names = ", ".join(lbl for lbl, _, _ in zero_high[:2])
                issues.append(f"{dim['label']}: {dim_total}/100 — 缺失: {names}")
            elif missed_high:
                names = ", ".join(lbl for lbl, _, _ in missed_high[:2])
                issues.append(f"{dim['label']}: {dim_total}/100 — 不足: {names}")
        else:
            all_zero = [lbl for lbl, earned, _ in missed_all if earned == 0]
            issues.append(f"{dim['label']}: {dim_total}/100 — 严重缺失: {', '.join(all_zero[:3])}")

    # Weighted total
    total = 0
    for dim in DIMENSIONS:
        total += dim_scores[dim["key"]] * dim["weight"]

    js_round = int(total + 0.5)

    return {
        "total": js_round,
        "dimensions": dim_scores,
        "items": all_items,
        "issues": issues,
        "strengths": strengths,
    }

# ── Schema Validation ──────────────────────────────────────────

def validate_loop_config(config: dict) -> list[str]:
    errors = []
    if "name" not in config or not config["name"]:
        errors.append("缺少必填字段: name")
    if "trigger" not in config:
        errors.append("缺少必填字段: trigger")
    else:
        t = config["trigger"].get("type")
        if t not in ("webhook","cron","manual","event"):
            errors.append(f"trigger.type 无效: '{t}'")
    if "pipeline" not in config or not config["pipeline"]:
        errors.append("缺少必填字段: pipeline")
    else:
        pl = config["pipeline"]
        if not isinstance(pl, list) or len(pl) == 0:
            errors.append("pipeline 必须是非空数组")
        else:
            for i, step in enumerate(pl):
                if "prompt" not in step and "parallel" not in step and "agents" not in step:
                    errors.append(f"pipeline[{i}] 缺少 prompt/parallel/agents")
                if "parallel" in step:
                    if not isinstance(step["parallel"], list) or len(step["parallel"]) == 0:
                        errors.append(f"pipeline[{i}].parallel 为空")
                    else:
                        for j, a in enumerate(step["parallel"]):
                            if "prompt" not in a:
                                errors.append(f"pipeline[{i}].parallel[{j}] 缺少 prompt")
                if "agents" in step:
                    if not isinstance(step["agents"], list) or len(step["agents"]) == 0:
                        errors.append(f"pipeline[{i}].agents 为空")
                    else:
                        for j, a in enumerate(step["agents"]):
                            if "prompt" not in a:
                                errors.append(f"pipeline[{i}].agents[{j}] 缺少 prompt")
    if "verify" in config:
        v = config["verify"]
        if "maker" not in v: errors.append("verify.maker 缺失")
        if "checker" not in v: errors.append("verify.checker 缺失")
    return errors

# ── Output rendering ──────────────────────────────────────────

BOLD = "\033[1m"; DIM = "\033[2m"; GREEN = "\033[92m"; YELLOW = "\033[93m"
CYAN = "\033[96m"; RED = "\033[91m"; RESET = "\033[0m"

def ok(s):  return f"{GREEN}{s}{RESET}"
def wrn(s): return f"{YELLOW}{s}{RESET}"
def err(s): return f"{RED}{s}{RESET}"
def bd(s):  return f"{BOLD}{s}{RESET}"
def dm(s):  return f"{DIM}{s}{RESET}"

# ── Main ───────────────────────────────────────────────────────

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--verbose", "-v", action="store_true", help="Show per-point breakdown")
    ap.add_argument("loop", nargs="?", help="Validate a specific loop only")
    args = ap.parse_args()

    target_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    project_file = None
    for c in ["loopcode.yaml", "loopcode.yml"]:
        p = os.path.join(target_dir, c)
        if os.path.exists(p):
            project_file = p
            break
    if not project_file:
        print(err("❌ 未找到 loopcode.yaml"))
        sys.exit(1)

    print(bd("=" * 70))
    print(bd("  LoopCode LRS Validator — Granular Scoring"))
    print(bd("=" * 70))
    print(f"  Project: {os.path.basename(project_file)}")

    with open(project_file, "r", encoding="utf-8") as f:
        yaml.safe_load(f)  # just check parseable

    loops_dir = os.path.join(target_dir, "loops")
    if not os.path.exists(loops_dir):
        print(err("\n❌ loops/ 目录不存在"))
        sys.exit(1)

    loop_files = sorted([
        f for f in os.listdir(loops_dir)
        if f.endswith(".yaml") or f.endswith(".yml")
    ])
    if args.loop:
        loop_files = [f for f in loop_files if f.startswith(args.loop)]
        if not loop_files:
            print(err(f"\n❌ 未找到匹配 '{args.loop}' 的 loop"))
            sys.exit(1)

    print(f"  Loops found: {len(loop_files)}")
    print()

    # Weight legend
    print(dm("  评分权重: 目标可量化20% | 终止条件20% | 验证机制15% | 失败恢复15%"))
    print(dm("            预算控制10% | 人工介入10% | 状态持久化10%"))
    print()

    results = []
    for fname in loop_files:
        fpath = os.path.join(loops_dir, fname)
        with open(fpath, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        if config is None:
            results.append({"name": fname, "valid": False, "errors": ["YAML 为空"], "lrs": None})
            continue

        schema_errs = validate_loop_config(config)
        if schema_errs:
            results.append({"name": config.get("name", fname), "valid": False, "errors": schema_errs, "lrs": None})
        else:
            lrs = calculate_lrs(config, target_dir, verbose=args.verbose)
            results.append({"name": config.get("name", fname), "valid": True, "errors": [], "lrs": lrs})

    # ── Print each loop ────────────────────────────────────────
    for i, r in enumerate(results):
        name = r["name"]
        if not r["lrs"]:
            print(f"\n{bd(f'[{i+1}] {name}')}  {err('❌ INVALID')}")
            for e in r["errors"]:
                print(f"    {err('•')} {e}")
            continue

        lrs = r["lrs"]
        grade = score_to_grade(lrs["total"])
        gicon = {"A": "🌟", "B": "✅", "C": "⚠️", "D": "🔶", "F": "🔴"}.get(grade, "❓")

        print(bd(f"\n{'─' * 70}"))
        print(bd(f"  [{i+1}] {name}  {gicon} LRS: {lrs['total']}/100 — Grade {grade}"))
        print(bd(f"{'─' * 70}"))

        # Dimension summary table
        print(f"  {'维度':<16s} {'得分':>5s}  {'权重':>5s}  {'加权':>6s}  {'进度'}")
        print(f"  {'─' * 16} {'─' * 5} {'─' * 5} {'─' * 6}  {'─' * 20}")
        for dim in DIMENSIONS:
            key = dim["key"]
            raw = lrs["dimensions"].get(key, 0)
            w = dim["weight"]
            weighted = raw * w
            bar_len = 20
            filled = int(raw / 100 * bar_len)
            bar_str = "█" * filled + "░" * (bar_len - filled)
            print(f"  {dim['label']:<16s} {raw:>4d}  {w:>4.0%}  {weighted:>5.1f}  {dm(bar_str)}")
        print()

        # Per-dimension itemized breakdown
        if args.verbose:
            for dim in DIMENSIONS:
                key = dim["key"]
                items = lrs["items"].get(key, [])
                dim_score = lrs["dimensions"].get(key, 0)
                print(f"  {bd('▸ ' + dim['label'])} ({dim_score}/100, 权重 {dim['weight']:.0%})")
                for label, earned, max_pts in items:
                    if earned == max_pts:
                        mark = ok("✓")
                    elif earned > 0:
                        mark = wrn(f"△ {earned}/{max_pts}")
                    else:
                        mark = err(f"✗ 0/{max_pts}")
                    print(f"    {mark}  {label:<38s} {dm(f'+{earned}')}")
                print()

        # Issues & strengths (compact)
        if lrs["issues"]:
            for issue in lrs["issues"]:
                print(f"  {wrn('⚠')}  {issue}")
        if lrs["strengths"]:
            for s in lrs["strengths"]:
                print(f"  {ok('✓')}  {s}")

    # ── Comparative table ──────────────────────────────────────
    if len(results) > 1:
        print(bd(f"\n{'═' * 70}"))
        print(bd("  Comparative Summary"))
        print(bd(f"{'═' * 70}"))
        header = f"  {'Loop':<32s}"
        for dim in DIMENSIONS:
            header += f" {dim['label']:<6s}"
        header += f" {'Total':>5s}  Grade"
        print(dm(header))
        print(dm("  " + "─" * (len(header) - 2)))
        for r in results:
            if not r["lrs"]: continue
            lrs = r["lrs"]
            row = f"  {r['name']:<32s}"
            for dim in DIMENSIONS:
                row += f" {lrs['dimensions'].get(dim['key'],0):>4d} "
            row += f" {lrs['total']:>4d}   {score_to_grade(lrs['total'])}"
            print(row)

        # Average
        valid_lrs = [r["lrs"] for r in results if r["lrs"]]
        if valid_lrs:
            avg_total = sum(l["total"] for l in valid_lrs) / len(valid_lrs)
            avg_row = f"  {'AVERAGE':<32s}"
            for dim in DIMENSIONS:
                avg_d = sum(l["dimensions"][dim["key"]] for l in valid_lrs) / len(valid_lrs)
                avg_row += f" {avg_d:>4.0f} "
            avg_row += f" {avg_total:>4.0f}   {score_to_grade(round(avg_total))}"
            print(dm(avg_row))

        print()

    sys.exit(0)

if __name__ == "__main__":
    main()
