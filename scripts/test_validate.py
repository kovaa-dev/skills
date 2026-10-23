"""Regression checks for repository validation and independently copied skills."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import validate


SOURCE = validate.ROOT


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.addCleanup(patch.stopall)
        patch.multiple(validate, ROOT=self.root, SKILLS_DIR=self.root / "skills").start()

    def write(self, relative, content):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def markdown_errors(self):
        errors = []
        validate.validate_markdown(errors)
        return errors

    def skill(self, interface):
        self.write("skills/example/SKILL.md", "---\nname: example\ndescription: Example skill.\n---\n# Example\n")
        self.write("skills/example/README.md", "# Example\n")
        self.write("skills/example/agents/openai.yaml", interface)

    def test_frontmatter_accepts_quoted_name_and_folded_description(self):
        path = self.write("SKILL.md", '---\nname: "example"\ndescription: >\n  First line\n  second line\n---\n# Example\n')
        errors = []
        name, description = validate.parse_frontmatter(path, errors)
        self.assertEqual(errors, [])
        self.assertEqual(name, "example")
        self.assertEqual(description.strip(), "First line second line")

    def test_frontmatter_rejects_malformed_yaml(self):
        path = self.write("SKILL.md", "---\nname: example\ndescription: Example\nbroken: [\n---\n")
        errors = []
        validate.parse_frontmatter(path, errors)
        self.assertTrue(errors)

    def test_ui_rejects_malformed_yaml(self):
        self.skill('interface:\n  display_name: "kovaa: example"\nbroken: [\n')
        errors = []
        validate.validate_skills(errors)
        self.assertTrue(errors)

    def test_display_name_must_belong_to_interface(self):
        self.skill('unrelated:\n  display_name: "kovaa: example"\n')
        errors = []
        validate.validate_skills(errors)
        self.assertTrue(errors)

    def test_missing_angle_bracket_destination(self):
        self.write("README.md", "[Missing](<absent.md>)\n")
        self.assertTrue(self.markdown_errors())

    def test_missing_reference_style_destination(self):
        self.write("README.md", "[Missing][target]\n\n[target]: absent.md\n")
        self.assertTrue(self.markdown_errors())

    def test_duplicate_heading_anchor(self):
        self.write("README.md", "## Example\n\n## Example\n\n[Second](#example-1)\n")
        self.assertEqual(self.markdown_errors(), [])

    def test_balanced_parentheses_and_space_in_destinations(self):
        self.write("reference(v2).md", "# Reference\n")
        self.write("reference v2.md", "# Reference\n")
        self.write("README.md", "[One](reference(v2).md)\n[Two](<reference v2.md>)\n")
        self.assertEqual(self.markdown_errors(), [])

    def test_inline_markup_and_setext_heading_anchors(self):
        self.write("README.md", "An `API_name`\n=============\n\n[Heading](#an-api_name)\n")
        self.assertEqual(self.markdown_errors(), [])

    def test_code_examples_do_not_create_real_links(self):
        examples = [
            "````md\n```md\n[Example](absent.md)\n```\n````\n",
            "> ```md\n> [Example](absent.md)\n> ```\n",
            "- ```md\n  [Example](absent.md)\n  ```\n",
            "    [Example](absent.md)\n",
        ]
        for example in examples:
            with self.subTest(example=example):
                self.write("README.md", example)
                self.assertEqual(self.markdown_errors(), [])

    def test_shorter_fence_does_not_close_longer_opening(self):
        self.write("README.md", "````md\nExample\n```\n")
        self.assertTrue(self.markdown_errors())

    def test_ignored_runtime_files_do_not_block_distribution(self):
        subprocess.run(["git", "init", "--quiet", str(self.root)], check=True)
        self.write(".gitignore", "/.agents/local/\n/.evidence/\n/node_modules/\n")
        self.write("README.md", "# Example\n")
        for relative in [".agents/local/handoff.md", ".evidence/result.md", "node_modules/dependency/README.md"]:
            self.write(relative, "Workspace: /home/fixture/project\n")
        self.assertEqual(self.markdown_errors(), [])
        self.write("new-document.md", "[Missing](absent.md)\n")
        self.assertTrue(self.markdown_errors(), "New nonignored documentation must still be checked")

    def test_existing_target_outside_repository_is_not_distributable(self):
        with tempfile.NamedTemporaryFile(dir=self.root.parent, suffix=".txt") as outside:
            relative = "../" + Path(outside.name).name
            self.write("README.md", f"[Outside]({relative})\n")
            self.assertTrue(self.markdown_errors())

    def test_skill_link_cannot_depend_on_repository_readme(self):
        self.write("README.md", "# Root guide\n")
        self.write("skills/example/README.md", "[Installation](../../README.md)\n")
        self.assertTrue(self.markdown_errors())

    def test_each_skill_remains_readable_after_standalone_copy(self):
        for source in sorted((SOURCE / "skills").iterdir()):
            if not (source / "SKILL.md").is_file():
                continue
            with self.subTest(skill=source.name):
                installed = self.root / "consumer" / ".agents" / "skills" / source.name
                shutil.copytree(source, installed, ignore=shutil.ignore_patterns("__pycache__"))
                with patch.multiple(validate, ROOT=installed, SKILLS_DIR=installed / "skills"):
                    self.assertEqual(self.markdown_errors(), [])

    def test_cli_accepts_exact_names(self):
        output = "◇  Found 2 skills\n◇  Available Skills\n│    example\n│    other\n"
        result = subprocess.CompletedProcess([], 0, output, "")
        with patch.object(validate.subprocess, "run", return_value=result):
            errors = []
            validate.validate_cli(["example", "other"], errors)
        self.assertEqual(errors, [])

    def test_cli_exit_zero_does_not_hide_missing_or_replaced_skill(self):
        outputs = [
            "◇  Found 1 skill\n│    example\n",
            "◇  Found 2 skills\n│    example\n│    unexpected\n",
            "Discovery output format changed\n",
        ]
        for output in outputs:
            with self.subTest(output=output):
                result = subprocess.CompletedProcess([], 0, output, "")
                with patch.object(validate.subprocess, "run", return_value=result):
                    errors = []
                    validate.validate_cli(["example", "other"], errors)
                self.assertTrue(errors)


if __name__ == "__main__":
    unittest.main()
