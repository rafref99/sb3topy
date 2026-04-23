#!/usr/bin/env python3

import argparse
import cProfile
import io
import os
import pstats
import sys

from sb3topy import config, main, pkg_log

def profile_conversion(project_path, output_path, autorun=False,
                       stats_file=None, limit=30, sort_by="cumulative",
                       no_assets=False, no_copy_engine=False,
                       parse_only=False, show_overall=False):
    """Profile a configurable sb3topy conversion run."""
    print(f"Profiling conversion of {project_path}...")

    profiler = cProfile.Profile()
    cli_args = [project_path, output_path]
    if autorun:
        cli_args.append("-r")

    config.parse_args(cli_args)
    config.LOG_LEVEL = 50
    if no_assets or parse_only:
        config.CONVERT_ASSETS = False
    if no_copy_engine or parse_only:
        config.COPY_ENGINE = False
    run_config = config.snapshot_config()
    pkg_log.config_logger()

    profiler.enable()
    try:
        main.run(run_config)
    except SystemExit:
        pass
    finally:
        profiler.disable()

    if stats_file:
        profiler.dump_stats(stats_file)
        print(f"Saved raw profile data to {stats_file}")

    print_profile_summary(
        profiler,
        limit=limit,
        sort_by=sort_by,
        show_overall=show_overall,
    )


def print_profile_summary(profiler, limit=30, sort_by="cumulative",
                          show_overall=False):
    """Print a project-focused profile summary."""
    print("Project hot paths:")
    print(project_hot_paths(profiler, limit=limit, sort_by=sort_by))

    if show_overall:
        overall_output = io.StringIO()
        overall_stats = pstats.Stats(profiler, stream=overall_output)
        overall_stats.strip_dirs().sort_stats(sort_by)
        overall_stats.print_stats(limit)
        print("Overall hot paths:")
        print(overall_output.getvalue())


def project_hot_paths(profiler, limit=30, sort_by="cumulative"):
    """Render the hottest project-local functions from a cProfile run."""
    stats = pstats.Stats(profiler)
    entries = []

    for func, stat in stats.stats.items():
        filename, lineno, func_name = func
        if not is_project_file(filename):
            continue

        primitive_calls, total_calls, total_time, cumulative_time, _ = stat
        entries.append({
            "filename": filename,
            "lineno": lineno,
            "func_name": func_name,
            "primitive_calls": primitive_calls,
            "total_calls": total_calls,
            "total_time": total_time,
            "cumulative_time": cumulative_time,
        })

    if sort_by == "time":
        key_name = "total_time"
    else:
        key_name = "cumulative_time"

    entries.sort(key=lambda item: item[key_name], reverse=True)
    entries = entries[:limit]

    output = io.StringIO()
    output.write(
        f"{len(stats.stats)} total profiled functions, "
        f"{sum(1 for func in stats.stats if is_project_file(func[0]))} project-local\n\n"
    )

    if not entries:
        output.write("No project-local functions matched the filter.\n")
        return output.getvalue()

    output.write(
        f"{'cumtime':>10} {'tottime':>10} {'calls':>12} location\n"
    )
    output.write(f"{'-' * 10} {'-' * 10} {'-' * 12} {'-' * 8}\n")
    for entry in entries:
        display_name = (
            f"{shorten_path(entry['filename'])}:{entry['lineno']}"
            f"({entry['func_name']})"
        )
        calls = format_calls(entry["primitive_calls"], entry["total_calls"])
        output.write(
            f"{entry['cumulative_time']:10.3f} "
            f"{entry['total_time']:10.3f} "
            f"{calls:>12} "
            f"{display_name}\n"
        )

    return output.getvalue()


def is_project_file(filename):
    """Return True when a profile row comes from this project."""
    normalized = filename.replace("\\", "/")
    return (
        "/src/sb3topy/" in normalized
        or "/src/engine/" in normalized
        or normalized.endswith("/profile_converter.py")
    )


def shorten_path(filename):
    """Trim unhelpful leading path segments from a profile row."""
    normalized = filename.replace("\\", "/")
    for marker in ("/src/sb3topy/", "/src/engine/", "/profile_converter.py"):
        if marker in normalized:
            return normalized.split(marker, 1)[1] if marker != "/profile_converter.py" else "profile_converter.py"
    return normalized


def format_calls(primitive_calls, total_calls):
    """Format primitive and total call counts compactly."""
    if primitive_calls == total_calls:
        return str(total_calls)
    return f"{primitive_calls}/{total_calls}"


def parse_args():
    """Parse command-line arguments for the profiling helper."""
    parser = argparse.ArgumentParser(description="Profile sb3topy conversion")
    parser.add_argument("project", help="Path to the .sb3 file")
    parser.add_argument(
        "--output",
        default="profile_output",
        help="Output directory for the converted project",
    )
    parser.add_argument(
        "-r",
        "--run",
        action="store_true",
        help="Run the converted project after profiling the conversion",
    )
    parser.add_argument(
        "--stats-file",
        help="Optional path to save raw cProfile stats data",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=30,
        help="Number of rows to print in the profile summary",
    )
    parser.add_argument(
        "--sort-by",
        default="cumulative",
        help="pstats sort key, for example: cumulative, time, calls",
    )
    parser.add_argument(
        "--no-assets",
        action="store_true",
        help="Skip asset conversion to focus on unpacking and parsing",
    )
    parser.add_argument(
        "--no-copy-engine",
        action="store_true",
        help="Skip copying the engine directory during profiling",
    )
    parser.add_argument(
        "--parse-only",
        action="store_true",
        help="Profile extraction and parsing only; skips assets and engine copy",
    )
    parser.add_argument(
        "--show-overall",
        action="store_true",
        help="Also print the unfiltered top rows, including runtime/library noise",
    )
    return parser.parse_args()


def main_cli():
    """CLI entry point for the profiling helper."""
    args = parse_args()

    if not os.path.exists(args.project):
        print(f"Error: Project file {args.project} not found.", file=sys.stderr)
        return 1

    profile_conversion(
        args.project,
        args.output,
        autorun=args.run,
        stats_file=args.stats_file,
        limit=args.limit,
        sort_by=args.sort_by,
        no_assets=args.no_assets,
        no_copy_engine=args.no_copy_engine,
        parse_only=args.parse_only,
        show_overall=args.show_overall,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main_cli())
