import argparse
from pathlib import Path

from .level_validation import validate_level_file
from .levels import get_default_levels


def _parse_args(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(description="Validate all configured pySNOOPY levels")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors (non-zero exit code).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    levels = get_default_levels()
    package_dir = Path(__file__).resolve().parent
    error_count = 0
    warning_count = 0

    for level in levels:
        result = validate_level_file(
            level_name=level.name,
            map_path=str((package_dir / level.map_path).resolve()),
            spawn_object_name=level.spawn_object_name,
            exit_object_name=level.exit_object_name,
            moving_hazard_object_name=level.moving_hazard_object_name,
            required_object_names=level.required_object_names,
        )

        print(f"[{level.name}] {level.map_path}")
        if result.is_valid and not result.warnings:
            print("  OK")

        for warning in result.warnings:
            warning_count += 1
            print(f"  WARNING: {warning}")

        for error in result.errors:
            error_count += 1
            print(f"  ERROR: {error}")

    if error_count > 0:
        print(f"Validation failed: {error_count} error(s), {warning_count} warning(s)")
        return 1

    if args.strict and warning_count > 0:
        print(f"Validation failed in strict mode: {warning_count} warning(s)")
        return 1

    print(f"Validation passed: {warning_count} warning(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
