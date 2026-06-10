"""
Check line lengths in Python files according to project conventions.
"""

import argparse
import sys
from pathlib import Path


def check_line_length(
        filepath: str, hardmax: int = 85, softmax: int | None = None,
    ) -> tuple[int, int, int]:
    """Check file for line length violations and whitespace issues.
        Returns (hard_violations, soft_warnings, whitespace_issues).
    """
    hard_violations: int = 0
    soft_warnings: int = 0
    whitespace_issues: int = 0

    hard_violation_lines: list[tuple[int, int, str]] = []
    soft_warning_lines: list[tuple[int, int, str]] = []
    whitespace_lines: list[int] = []

    path = Path(filepath)
    if not path.exists():
        print(f"Error: File not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    in_docstring: bool = False
    docstring_delimiter: str | None = None

    for line_num, line in enumerate(lines, start=1):
        line_len = len(line.rstrip("\n\r"))

        if line.rstrip("\n\r \t") != line.rstrip("\n\r"):
            whitespace_lines.append(line_num)
            whitespace_issues += 1

        stripped = line.strip()

        if stripped:
            if  (   not in_docstring
                    and (   stripped.startswith('"""')
                            or stripped.startswith("'''")
                        )
                ):
                if stripped.count('"""') >= 2 or stripped.count("'''") >= 2:
                    pass
                else:
                    in_docstring = True
                    docstring_delimiter = "'''"
                    if stripped.startswith('"""'):
                        docstring_delimiter = '"""'
            elif(   in_docstring
                    and (   stripped.endswith(docstring_delimiter)
                            or stripped.endswith(docstring_delimiter + ':')
                        )
                ):
                in_docstring = False
                docstring_delimiter = None

        limit = hardmax
        if in_docstring or (docstring_delimiter is not None):
            limit = 72

        if line_len > limit:
            preview = line[: min(line_len, 60)].rstrip("\n\r")
            hard_violation_lines.append((line_num, line_len, preview))
            hard_violations += 1

        if not in_docstring and softmax is not None and line_len > softmax:
            if line_len <= hardmax:
                preview = line[: min(line_len, 60)].rstrip("\n\r")
                soft_warning_lines.append((line_num, line_len, preview))
                soft_warnings += 1

    print(f"File: {filepath}\n")

    if hard_violation_lines:
        print("HARD VIOLATIONS:")
        for line_num, line_len, preview in hard_violation_lines:
            print(f"  Line {line_num} ({line_len} chars): {preview}...")
        print()

    if soft_warning_lines and softmax is not None:
        print(f"SOFT WARNINGS (--softmax={softmax}):")
        for line_num, line_len, preview in soft_warning_lines:
            print(f"  Line {line_num} ({line_len} chars): {preview}...")
        print()

    if whitespace_lines:
        print("WHITESPACE ISSUES:")
        for line_num in whitespace_lines:
            print(f"  Line {line_num}: trailing whitespace detected")
        print()

    summary_parts = []
    if hard_violations:
        summary_parts.append(f"{hard_violations} hard violation(s)")
    if soft_warnings:
        summary_parts.append(f"{soft_warnings} soft warning(s)")
    if whitespace_issues:
        summary_parts.append(f"{whitespace_issues} whitespace issue(s)")

    if summary_parts:
        print(f"SUMMARY: {', '.join(summary_parts)}")
    else:
        print("SUMMARY: No issues found")

    return hard_violations, soft_warnings, whitespace_issues


def main() -> None:
    """Parse arguments and run line length checker."""
    parser = argparse.ArgumentParser(
        description="Check line lengths in Python files"
    )
    parser.add_argument(
        "filepath",
        help="Relative path to the file to check"
    )
    parser.add_argument(
        "--hardmax",
        type=int,
        default=85,
        help="Hard maximum line length for code (default: 85)"
    )
    parser.add_argument(
        "--softmax",
        type=int,
        default=None,
        help="Soft maximum line length for code (optional, "
             "default: no soft warnings)"
    )

    args = parser.parse_args()

    hard_violations, soft_warnings, whitespace_issues = check_line_length(
        args.filepath,
        args.hardmax,
        args.softmax
    )

    if hard_violations > 0 or whitespace_issues > 0:
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
