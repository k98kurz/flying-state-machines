from __future__ import annotations
from .version import __version__
from importlib.resources import files
from pathlib import Path
import argparse


def _write_skill_to_dir(output_dir: str) -> None:
    """Write the FSM agent skill and references to an output directory."""
    skill_md = (files('flying_state_machines') / 'skill/SKILL.md').read_text()
    references_dir = files('flying_state_machines') / 'skill/references'
    references = []
    if references_dir.is_dir():
        references = [r for r in references_dir.iterdir() if r.is_file()]

    output_path = Path(output_dir).resolve() / 'flying-state-machines'
    output_path.mkdir(parents=True, exist_ok=True)
    (output_path / 'SKILL.md').write_text(skill_md)
    if references:
        refs_out = output_path / 'references'
        refs_out.mkdir(exist_ok=True)
        for ref in references:
            (refs_out / ref.name).write_bytes(ref.read_bytes())
    print(f"Skill copied to {output_path}/SKILL.md")


def get_skill_command(output_dir: str | None = None) -> None:
    """Output the FSM agent skill."""
    if output_dir:
        _write_skill_to_dir(output_dir)
    else:
        skill_md = (files('flying_state_machines') / 'skill/SKILL.md').read_text()
        dox_md = (files('flying_state_machines') / 'skill/references/dox.md').read_text()
        print(skill_md)
        print("\n-----\n")
        print(dox_md)


def opencode_skill_command() -> None:
    """Output the FSM agent skill for OpenCode."""
    _write_skill_to_dir('.opencode/skills')
    print("Restart OpenCode to make it available to agents")


def cursor_skill_command() -> None:
    """Output the FSM agent skill for Cursor."""
    _write_skill_to_dir('.cursor/skills')


def claude_skill_command() -> None:
    """Output the FSM agent skill for Claude Code."""
    _write_skill_to_dir('.claude/skills')


def codex_skill_command() -> None:
    """Output the FSM agent skill for Codex."""
    _write_skill_to_dir('.agents/skills')


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog='fsm',
        description='Flying State Machine skill export command'
    )
    parser.add_argument(
        "--version", action="version", version=__version__,
    )

    subparsers = parser.add_subparsers(
        dest='command',
        help='Available commands',
        title='commands',
        description='Subcommands for FSM'
    )

    # Create skill subcommand parser (shared for all aliases)
    skill_parser = argparse.ArgumentParser(add_help=False)
    skill_parser.add_argument(
        '--output', '-o',
        help='Output directory (default: print to stdout)',
        default=None
    )

    # Add subcommands
    subparsers.add_parser(
        'skill',
        parents=[skill_parser],
        help='skill [--output path] [-O path]: Output the FSM agent skill '
            'to stdout or an output path',
        description=f'Output the FSM agent skill'
    )

    subparsers.add_parser(
        'opencode',
        parents=[skill_parser],
        help='opencode: Install the FSM agent skill compatibly with OpenCode',
        description=f'Output the FSM agent skill for OpenCode'
    )

    subparsers.add_parser(
        'claude',
        parents=[skill_parser],
        help='claude: Install the FSM agent skill compatibly with Claude Code',
        description=f'Output the FSM agent skill for Claude Code'
    )

    subparsers.add_parser(
        'cursor',
        parents=[skill_parser],
        help='cursor: Install the FSM agent skill compatibly with Cursor',
        description=f'Output the FSM agent skill for Cursor'
    )

    subparsers.add_parser(
        'codex',
        parents=[skill_parser],
        help='codex: Install the FSM agent skill compatibly with Codex',
        description=f'Output the FSM agent skill for Codex'
    )

    args = parser.parse_args()

    if args.command == 'skill':
        get_skill_command(args.output)
    elif args.command == 'opencode':
        opencode_skill_command()
    elif args.command == 'cursor':
        cursor_skill_command()
    elif args.command == 'claude':
        claude_skill_command()
    elif args.command == 'codex':
        codex_skill_command()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
