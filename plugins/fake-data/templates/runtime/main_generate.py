#!/usr/bin/env python3
"""
FAKE_DATA log generator orchestrator.

Discovers generators in fake_data/generators/, sorts them by dependency
order, and runs them to produce log files in fake_data/output/.

Usage:
    python3 fake_data/main_generate.py [--sources=all] [--days=31] [--quiet]
    python3 fake_data/main_generate.py --list
    python3 fake_data/main_generate.py --show-files
    python3 fake_data/main_generate.py --help
"""

import argparse
import importlib
import pkgutil
import sys
import time as time_mod
from pathlib import Path
from typing import Dict, List, Any, Optional

# Bootstrap: ensure fake_data package is importable regardless of cwd
_script_dir = Path(__file__).resolve().parent
_repo_root = _script_dir.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

# Version gate
if sys.version_info < (3, 9):
    print("ERROR: FAKE_DATA requires Python 3.9+. "
          f"You are running {sys.version_info.major}.{sys.version_info.minor}.",
          file=sys.stderr)
    sys.exit(1)

from fake_data.config import DEFAULT_START_DATE, DEFAULT_DAYS, DEFAULT_SCALE


def discover_generators() -> Dict[str, Any]:
    """Scan fake_data/generators/ for modules with SOURCE_META."""
    generators_dir = _script_dir / "generators"
    if not generators_dir.exists():
        return {}

    discovered = {}
    for finder, name, is_pkg in pkgutil.iter_modules([str(generators_dir)]):
        if name.startswith("_"):
            continue
        try:
            module = importlib.import_module(f"fake_data.generators.{name}")
        except (ImportError, SyntaxError) as e:
            print(f"WARNING: Could not import generators/{name}.py: {e}",
                  file=sys.stderr)
            continue

        meta = getattr(module, "SOURCE_META", None)
        if meta is None:
            print(f"WARNING: generators/{name}.py has no SOURCE_META, skipping.",
                  file=sys.stderr)
            continue

        source_id = meta.get("source_id", name.replace("generate_", ""))
        discovered[source_id] = module

    return discovered


def topological_sort(discovered: Dict[str, Any]) -> List[str]:
    """Sort source_ids by depends_on order. Raises ValueError on cycles."""
    graph = {}
    for sid, mod in discovered.items():
        deps = mod.SOURCE_META.get("depends_on", [])
        graph[sid] = [d for d in deps if d in discovered]

    visited = set()
    temp_mark = set()
    order = []

    def visit(node: str):
        if node in temp_mark:
            raise ValueError(f"Dependency cycle detected involving '{node}'")
        if node in visited:
            return
        temp_mark.add(node)
        for dep in graph.get(node, []):
            visit(dep)
        temp_mark.remove(node)
        visited.add(node)
        order.append(node)

    for node in graph:
        visit(node)

    return order


def _progress_callback(source_id: str, day: int, total_days: int):
    """Print single-line progress update."""
    sys.stdout.write(f"\r  {source_id}: day {day + 1}/{total_days}   ")
    sys.stdout.flush()


def run_generators(discovered: Dict[str, Any], order: List[str],
                   args: argparse.Namespace) -> Dict[str, Any]:
    """Execute generators in order. Returns results dict."""
    results = {"success": {}, "errors": {}, "total_events": 0}
    total = len(order)

    for idx, source_id in enumerate(order, 1):
        module = discovered[source_id]
        meta = module.SOURCE_META
        func_name = f"generate_{source_id}_logs"
        func = getattr(module, func_name, None)

        if func is None:
            results["errors"][source_id] = f"Function {func_name}() not found"
            continue

        if not args.quiet:
            print(f"[{idx}/{total}] {source_id} ({meta.get('category', '?')})...")

        start_time = time_mod.time()
        try:
            result = func(
                start_date=args.start_date,
                days=args.days,
                scale=args.scale,
                scenarios=args.scenarios,
                seed=args.seed,
                progress_callback=None if args.quiet else _progress_callback,
                quiet=args.quiet,
            )
            elapsed = time_mod.time() - start_time

            if isinstance(result, dict):
                event_count = result.get("total", 0)
            else:
                event_count = result or 0

            results["success"][source_id] = {
                "events": event_count,
                "elapsed": elapsed,
            }
            results["total_events"] += event_count

            if not args.quiet:
                print(f"\r  {source_id}: {event_count:,} events "
                      f"in {elapsed:.1f}s")

        except Exception as e:
            elapsed = time_mod.time() - start_time
            results["errors"][source_id] = str(e)
            if not args.quiet:
                print(f"\r  {source_id}: ERROR after {elapsed:.1f}s -- {e}",
                      file=sys.stderr)

    return results


def cmd_list(discovered: Dict[str, Any]):
    """Print a table of registered generators."""
    if not discovered:
        print("No generators registered. Run /fake-data:add-generator to create one.")
        return

    print(f"\n{'Source ID':<20} {'Category':<15} {'Depends On':<20} Description")
    print("-" * 80)
    for sid in sorted(discovered.keys()):
        meta = discovered[sid].SOURCE_META
        deps = ", ".join(meta.get("depends_on", [])) or "-"
        desc = meta.get("description", "")[:30]
        print(f"{sid:<20} {meta.get('category', '?'):<15} {deps:<20} {desc}")
    print(f"\n{len(discovered)} generator(s) registered.")


def cmd_show_files(discovered: Dict[str, Any]):
    """Print expected output files for all generators."""
    if not discovered:
        print("No generators registered.")
        return

    print("\nExpected output files:")
    for sid in sorted(discovered.keys()):
        meta = discovered[sid].SOURCE_META
        cat = meta.get("category", "unknown")
        print(f"  {sid}: output/{cat}/{sid}.log")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="FAKE_DATA log generator orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 fake_data/main_generate.py --days=7 --quiet
  python3 fake_data/main_generate.py --sources=asa,aws --days=14
  python3 fake_data/main_generate.py --list
        """,
    )
    parser.add_argument("--sources", default="all",
                        help="Comma-separated source IDs, or 'all' (default: all)")
    parser.add_argument("--days", type=int, default=DEFAULT_DAYS,
                        help=f"Days to generate (default: {DEFAULT_DAYS})")
    parser.add_argument("--start-date", default=DEFAULT_START_DATE,
                        help=f"Start date YYYY-MM-DD (default: {DEFAULT_START_DATE})")
    parser.add_argument("--scale", type=float, default=DEFAULT_SCALE,
                        help=f"Volume scaling factor (default: {DEFAULT_SCALE})")
    parser.add_argument("--scenarios", default="none",
                        help="Scenario list (reserved for future use)")
    parser.add_argument("--seed", type=int, default=None,
                        help="Deterministic seed for baseline event generation. "
                             "Same seed + same workspace = identical output, "
                             "useful for A/B testing Splunk configs. Scenarios "
                             "remain deterministic via their own scenario_id hash.")
    parser.add_argument("--list", action="store_true",
                        help="List registered generators and exit")
    parser.add_argument("--show-files", action="store_true",
                        help="Show expected output files and exit")
    parser.add_argument("--quiet", action="store_true",
                        help="Suppress progress output")
    parser.add_argument("--test", action="store_true",
                        help="(Reserved for Splunk integration)")
    parser.add_argument("--no-test", action="store_true",
                        help="(Reserved for Splunk integration)")
    parser.add_argument("--tui", action="store_true",
                        help="Launch interactive TUI")

    args = parser.parse_args()

    # Reserved flags
    if args.test or args.no_test:
        print("--test/--no-test flags are reserved for the upcoming "
              "Splunk integration plan.", file=sys.stderr)
        print("In the current version, all output goes to fake_data/output/.",
              file=sys.stderr)
        sys.exit(2)

    if args.tui:
        from fake_data.tui_generate import main as tui_main
        tui_main()
        return

    # Verify workspace
    try:
        from fake_data.manifest import FAKE_DATA_WORKSPACE_VERSION
        if FAKE_DATA_WORKSPACE_VERSION > 1:
            print(f"WARNING: This workspace uses schema version "
                  f"{FAKE_DATA_WORKSPACE_VERSION}, but this orchestrator "
                  f"only understands version 1. Some features may not work.",
                  file=sys.stderr)
    except ImportError:
        print("ERROR: fake_data/manifest.py not found. Is this a "
              "FAKE_DATA workspace?", file=sys.stderr)
        print("Run /fake-data:init to create one.", file=sys.stderr)
        sys.exit(1)

    # Discover
    discovered = discover_generators()

    # Info commands
    if args.list:
        cmd_list(discovered)
        return

    if args.show_files:
        cmd_show_files(discovered)
        return

    # Filter sources
    if args.sources != "all":
        requested = set(s.strip() for s in args.sources.split(","))
        missing = requested - set(discovered.keys())
        if missing:
            print(f"ERROR: Unknown source(s): {', '.join(sorted(missing))}",
                  file=sys.stderr)
            print(f"Available: {', '.join(sorted(discovered.keys()))}",
                  file=sys.stderr)
            sys.exit(1)
        to_run = set(requested)
        changed = True
        while changed:
            changed = False
            for sid in list(to_run):
                deps = discovered[sid].SOURCE_META.get("depends_on", [])
                for dep in deps:
                    if dep in discovered and dep not in to_run:
                        to_run.add(dep)
                        changed = True
        discovered = {k: v for k, v in discovered.items() if k in to_run}

    if not discovered:
        print("No generators to run. Use /fake-data:add-generator to create one.")
        return

    # Sort and run
    try:
        order = topological_sort(discovered)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    if not args.quiet:
        print(f"\nFAKE_DATA Generator -- {len(order)} source(s), "
              f"{args.days} days, scale {args.scale}x\n")

    overall_start = time_mod.time()
    results = run_generators(discovered, order, args)
    overall_elapsed = time_mod.time() - overall_start

    if not args.quiet:
        print(f"\n{'=' * 50}")
        print(f"Total: {results['total_events']:,} events "
              f"in {overall_elapsed:.1f}s")
        if results["errors"]:
            print(f"Errors ({len(results['errors'])}):")
            for sid, err in results["errors"].items():
                print(f"  {sid}: {err}")
        print()


if __name__ == "__main__":
    main()
