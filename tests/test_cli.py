from importlib.resources import files
from pathlib import Path
import contextlib
import io
import tempfile
import unittest

from flying_state_machines import cli


class TestSkillExport(unittest.TestCase):
    def _read_expected_skill_and_dox(self):
        skill_md = (files('flying_state_machines') / 'skill/SKILL.md').read_text()
        dox_md = (
            files('flying_state_machines') / 'skill/references/dox.md'
        ).read_text()
        dox_bytes = (
            files('flying_state_machines') / 'skill/references/dox.md'
        ).read_bytes()
        return skill_md, dox_md, dox_bytes

    def test_write_skill_to_dir_writes_skill_and_references(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cli._write_skill_to_dir(temp_dir)

            output_path = Path(temp_dir) / 'flying-state-machines'
            skill_path = output_path / 'SKILL.md'
            dox_path = output_path / 'references' / 'dox.md'

            self.assertTrue(skill_path.is_file())
            self.assertTrue(dox_path.is_file())

            skill_md, _, dox_bytes = self._read_expected_skill_and_dox()

            self.assertEqual(skill_path.read_text(), skill_md)
            self.assertEqual(dox_path.read_bytes(), dox_bytes)

    def test_get_skill_command_with_output_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cli.get_skill_command(temp_dir)

            output_path = Path(temp_dir) / 'flying-state-machines'
            skill_path = output_path / 'SKILL.md'
            dox_path = output_path / 'references' / 'dox.md'

            self.assertTrue(skill_path.is_file())
            self.assertTrue(dox_path.is_file())

            skill_md, _, dox_bytes = self._read_expected_skill_and_dox()

            self.assertEqual(skill_path.read_text(), skill_md)
            self.assertEqual(dox_path.read_bytes(), dox_bytes)

    def test_get_skill_command_stdout_includes_separator_and_dox(self):
        skill_md, dox_md, _ = self._read_expected_skill_and_dox()

        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            cli.get_skill_command(None)

        output = buffer.getvalue()
        expected = f"{skill_md}\n\n-----\n\n{dox_md}\n"
        self.assertEqual(output, expected)


if __name__ == "__main__":
    unittest.main()
