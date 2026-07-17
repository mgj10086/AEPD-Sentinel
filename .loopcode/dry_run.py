#!/usr/bin/env python3
"""
LoopCode Dry-Run Simulator for AE Sentinel
Simulates loop execution without making actual LLM calls.
Usage: python3 .loopcode/dry_run.py [loop-name]
       python3 .loopcode/dry_run.py              # runs all loops
       python3 .loopcode/dry_run.py ae-coding-review  # runs one
"""

import os
import sys
import time
import yaml
from pathlib import Path

# ── Color helpers ──────────────────────────────────────────────

BOLD = "\033[1m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RED = "\033[91m"
RESET = "\033[0m"
DIM = "\033[2m"

def ok(s):    return f"{GREEN}[ok]{RESET} {s}"
def warn(s):  return f"{YELLOW}[!!]{RESET} {s}"
def dim(s):   return f"{DIM}{s}{RESET}"
def bold(s):  return f"{BOLD}{s}{RESET}"
def cyan(s):  return f"{CYAN}{s}{RESET}"
def section(s): return f"\n{CYAN}── {s} {RESET}{'─' * (50 - len(s))}"

# ── Dry Run Engine ─────────────────────────────────────────────

class DryRunEngine:
    def __init__(self, target_dir: str):
        self.target_dir = Path(target_dir)
        self.loops_dir = self.target_dir / "loops"

    def find_loop(self, loop_name: str) -> dict:
        for ext in ["yaml", "yml"]:
            path = self.loops_dir / f"{loop_name}.{ext}"
            if path.exists():
                with open(path) as f:
                    return yaml.safe_load(f)
        raise FileNotFoundError(f"Loop '{loop_name}' not found in loops/")

    def list_loops(self) -> list[str]:
        if not self.loops_dir.exists():
            return []
        return sorted([
            f.replace(".yaml", "").replace(".yml", "")
            for f in os.listdir(self.loops_dir)
            if f.endswith(".yaml") or f.endswith(".yml")
        ])

    def run_loop(self, loop_name: str) -> dict:
        config = self.find_loop(loop_name)
        start_time = time.time()

        print()
        print("=" * 60)
        print(bold(f"  Running Loop: {loop_name}"))
        print("=" * 60)
        print(f"Config: loops/{loop_name}.yaml")

        # Pipeline info
        pipeline = config.get("pipeline", [])
        total_agents = 0
        for step in pipeline:
            if "parallel" in step:
                total_agents += len(step["parallel"])
            elif "agents" in step:
                total_agents += len(step["agents"])
            else:
                total_agents += 1

        verify = config.get("verify")
        if verify:
            makers = verify.get("maker", [])
            makers_str = makers if isinstance(makers, str) else ", ".join(makers)
            checkers = verify.get("checker", "")
            checkers_str = checkers if isinstance(checkers, str) else ", ".join(checkers)
            print(f"Pipeline: {len(pipeline)} step(s), {total_agents} agent(s)")
            print(f"{bold('Verification:')} Maker=[{makers_str}] | Checker={checkers_str}")

        # ── Pipeline Execution ──────────────────────────────────
        print(section("Pipeline Execution"))

        for i, step in enumerate(pipeline):
            if "parallel" in step:
                agents = step["parallel"]
                print(f"\n  {bold(f'Step {i+1}:')} Running {len(agents)} agents in parallel...")
                for j, agent in enumerate(agents):
                    label = agent.get("label", f"Agent {j+1}")
                    prompt_preview = agent.get("prompt", "")[:60].replace("\n", " ")
                    print(f"  {dim('->')} Agent: {cyan(label)}")
                    if prompt_preview:
                        print(f"     {dim(prompt_preview + '...')}")
                    # Simulate work
                    duration_ms = 80 + (hash(label) % 200)
                    time.sleep(0.05)
                    print(f"    {ok(f'Completed ({duration_ms}ms, 0 up/0 down tokens, $0.0000)')}")

            elif "agents" in step:
                agents = step["agents"]
                print(f"\n  {bold(f'Step {i+1}:')} Sequential ({len(agents)} agents)...")
                for j, agent in enumerate(agents):
                    label = agent.get("label", f"Agent {j+1}")
                    print(f"  {dim('->')} Agent: {cyan(label)}...")
                    time.sleep(0.05)
                    print(f"    {ok(f'Completed (95ms, 0 up/0 down tokens, $0.0000)')}")

            else:
                label = step.get("label", f"Agent {i+1}")
                print(f"\n  {bold(f'Step {i+1}:')} Single agent...")
                print(f"  {dim('->')} Agent: {cyan(label)}...")
                time.sleep(0.05)
                print(f"    {ok('Completed (85ms, 0 up/0 down tokens, $0.0000)')}")

        # ── Maker/Checker Verification ──────────────────────────
        if verify:
            print(section("Maker/Checker Verification"))

            max_rounds = verify.get("maxRounds", 3)
            auto_retry = verify.get("autoRetry", True)
            makers_list = verify.get("maker", [])
            if isinstance(makers_list, str):
                makers_list = [makers_list]
            checkers_list = verify.get("checker", [])
            if isinstance(checkers_list, str):
                checkers_list = [checkers_list]

            print(f"  Maker(s):   {', '.join(makers_list)}")
            print(f"  Checker(s): {', '.join(checkers_list)}")
            print(f"  Max rounds: {max_rounds}")
            print(f"  Auto-retry: {auto_retry}")
            print()

            # Simulate verification (always passes in dry run, like real dry_run)
            for round_num in range(1, min(2, max_rounds + 1)):
                print(f"  Round {round_num}: {ok('PASS')} (score: 0.95)")
                time.sleep(0.08)

            print(f"\n  {ok('Verification passed — all checks green')}")

        # ── State Persistence ───────────────────────────────────
        memory = config.get("memory")
        if memory:
            state_dir = self.target_dir / memory.get("path", ".loopcode/state")
            state_dir.mkdir(parents=True, exist_ok=True)
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            state_file = state_dir / f"{loop_name}-{timestamp}.json"
            import json
            state_file.write_text(json.dumps({
                "loop": loop_name,
                "status": "completed",
                "timestamp": timestamp,
                "mode": "dry_run",
            }, indent=2))
            print(f"\n  {dim('State saved:')} {state_file.name}")

        # ── Results ─────────────────────────────────────────────
        duration = int((time.time() - start_time) * 1000)

        # Budget est.
        budget = config.get("budget", {})
        max_tokens = budget.get("maxTokens", 500000)
        max_duration = budget.get("maxDurationMinutes", 30)
        est_cost = round(total_agents * 0.015, 4)

        print(section("Results"))
        success_msg = ok("Loop '{}' completed successfully".format(loop_name))
        print(f"  {success_msg}")
        print(f"  Duration: {duration}ms")
        print(f"  Steps: {total_agents}")
        print(f"  Est. Cost: ${est_cost:.4f} (dry run: $0.0000)")
        print(f"  Budget: {max_tokens:,} tokens / {max_duration}min")

        return {
            "loop_name": loop_name,
            "success": True,
            "duration_ms": duration,
            "agents": total_agents,
            "verified": verify is not None,
        }

# ── Main ───────────────────────────────────────────────────────

def main():
    target_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    engine = DryRunEngine(target_dir)

    available = engine.list_loops()

    # Determine which loop(s) to run
    if len(sys.argv) > 1:
        requested = sys.argv[1]
        if requested in available:
            loops_to_run = [requested]
        else:
            print(f"❌ Loop '{requested}' not found.")
            print(f"   Available: {', '.join(available)}")
            sys.exit(1)
    else:
        loops_to_run = available

    if not loops_to_run:
        print("❌ No loops found in loops/")
        sys.exit(1)

    print(bold("\n🏥 AE Sentinel — LoopCode Dry Run"))
    print(dim(f"   Project: {target_dir}"))
    print(dim(f"   Mode: Dry run (no LLM calls, no cost)"))

    # Run each loop
    results = []
    for loop_name in loops_to_run:
        try:
            result = engine.run_loop(loop_name)
            results.append(result)
        except Exception as e:
            print(f"\n❌ Error running '{loop_name}': {e}")

    # Final summary
    print(f"\n{'═' * 60}")
    if results:
        total_agents = sum(r["agents"] for r in results)
        total_duration = sum(r["duration_ms"] for r in results)
        verified_count = sum(1 for r in results if r["verified"])

        print(f"""  {bold('Dry Run Summary')}
  Loops executed:  {len(results)}
  Total agents:    {total_agents}
  Verified loops:  {verified_count}/{len(results)}
  Total duration:  {total_duration}ms
  Actual cost:     $0.0000 (dry run)

  {ok('All loops executed successfully.')}
  {dim('Remove --dry-run to execute with real LLM calls.')}""")
    print(f"{'═' * 60}")

if __name__ == "__main__":
    main()
