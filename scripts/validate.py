#!/usr/bin/env python3
"""Validate repository metadata, Markdown, skill packages, and optional CLI discovery."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

import yaml
from markdown_it import MarkdownIt
from markdown_it.token import Token

ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / "skills"
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)
CYRILLIC_RE = re.compile(r"[А-Яа-яЁё]")
LOCAL_PATH_RE = re.compile(r"(?:/Users/[^/<\s]+|/home/[^/<\s]+|[A-Za-z]:\\Users\\[^\\<\s]+)")
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---(?:\n|$)", re.DOTALL)
ACTION_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def github_slug(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^\w\- ]", "", value, flags=re.UNICODE)
    return value.replace(" ", "-")


def yaml_mapping(text: str, path: Path, errors: list[str]) -> dict:
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        errors.append(f"{path.relative_to(ROOT)}: invalid YAML: {exc}")
        return {}
    if not isinstance(data, dict):
        errors.append(f"{path.relative_to(ROOT)}: YAML must contain a mapping")
        return {}
    return data


def parse_frontmatter(path: Path, errors: list[str]) -> tuple[str, str]:
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        errors.append(f"{path.relative_to(ROOT)}: missing YAML frontmatter")
        return "", ""

    data = yaml_mapping(match.group(1), path, errors)
    name, description = data.get("name"), data.get("description")
    if not isinstance(name, str) or not name.strip():
        errors.append(f"{path.relative_to(ROOT)}: frontmatter name must be a nonempty string")
        name = ""
    if not isinstance(description, str) or not description.strip():
        errors.append(f"{path.relative_to(ROOT)}: frontmatter description must be a nonempty string")
        description = ""
    return name, " ".join(description.split())


def validate_skills(errors: list[str]) -> list[str]:
    if not SKILLS_DIR.is_dir():
        errors.append("skills/: directory is missing")
        return []

    skill_dirs = sorted(path for path in SKILLS_DIR.iterdir() if path.is_dir())
    names: list[str] = []
    for directory in skill_dirs:
        skill_file = directory / "SKILL.md"
        if not skill_file.is_file():
            errors.append(f"skills/{directory.name}: SKILL.md is missing")
            continue
        name, description = parse_frontmatter(skill_file, errors)
        names.append(name)
        if not NAME_RE.fullmatch(name):
            errors.append(f"{skill_file.relative_to(ROOT)}: invalid skill name {name!r}")
        if name != directory.name:
            errors.append(
                f"{skill_file.relative_to(ROOT)}: name {name!r} does not match directory {directory.name!r}"
            )
        if not description:
            errors.append(f"{skill_file.relative_to(ROOT)}: description is empty")
        elif len(description) > 1024:
            errors.append(
                f"{skill_file.relative_to(ROOT)}: description is {len(description)} characters; maximum is 1024"
            )
        if not (directory / "README.md").is_file():
            errors.append(f"skills/{directory.name}: README.md is missing")
        interface_file = directory / "agents" / "openai.yaml"
        if not interface_file.is_file():
            errors.append(f"skills/{directory.name}: agents/openai.yaml is missing")
            continue
        data = yaml_mapping(interface_file.read_text(encoding="utf-8"), interface_file, errors)
        interface = data.get("interface")
        if not isinstance(interface, dict):
            errors.append(f"{interface_file.relative_to(ROOT)}: interface must be a mapping")
            continue
        display_name = interface.get("display_name")
        if not isinstance(display_name, str) or not display_name:
            errors.append(
                f"{interface_file.relative_to(ROOT)}: interface.display_name must be a nonempty string"
            )
        elif not display_name.startswith("kovaa: ") or display_name != display_name.lower():
            errors.append(
                f"{interface_file.relative_to(ROOT)}: display_name must be lowercase and start with 'kovaa: '"
            )
    return sorted(name for name in names if name)


def markdown_files() -> list[Path]:
    try:
        top = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"], cwd=ROOT, capture_output=True, text=True
        )
    except FileNotFoundError:
        top = None
    if top and top.returncode == 0 and Path(top.stdout.strip()).resolve() == ROOT:
        result = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z", "--", "*.md"],
            cwd=ROOT, capture_output=True, text=True, check=True,
        )
        return sorted({
            ROOT / name for name in result.stdout.split("\0")
            if name and (ROOT / name).is_file()
        })
    # An exported repository has no Git ignore state; inspect its distribution trees.
    if (ROOT / "SKILL.md").is_file():
        return sorted(ROOT.rglob("*.md"))
    return sorted((*ROOT.glob("*.md"), *(ROOT / "skills").rglob("*.md")))


def inline_text(tokens: list[Token]) -> str:
    parts: list[str] = []
    for token in tokens:
        if token.children:
            parts.append(inline_text(token.children))
        elif token.type in {"text", "code_inline"}:
            parts.append(token.content)
        elif token.type in {"softbreak", "hardbreak"}:
            parts.append(" ")
    return "".join(parts)


def validate_markdown(errors: list[str]) -> int:
    files = markdown_files()
    links_by_path: dict[Path, list[str]] = {}
    headings_by_path: dict[Path, set[str]] = {}
    parser = MarkdownIt("commonmark")

    for path in files:
        text = path.read_text(encoding="utf-8")
        relative = path.relative_to(ROOT)
        if CYRILLIC_RE.search(text):
            errors.append(f"{relative}: Cyrillic text remains")
        local_path = LOCAL_PATH_RE.search(text)
        if local_path:
            errors.append(f"{relative}: machine-local absolute path {local_path.group(0)!r}")
        body = FRONTMATTER_RE.sub("", text, count=1) if path.name == "SKILL.md" else text
        tokens = parser.parse(body)
        headings: set[str] = set()
        links: list[str] = []
        for index, token in enumerate(tokens):
            if token.type == "fence" and token.map:
                # A closed fence spans its body lines plus opening and closing lines.
                if token.map[1] - token.map[0] < token.content.count("\n") + 2:
                    errors.append(f"{relative}: unclosed fenced block")
            if token.type == "heading_open":
                slug = github_slug(inline_text(tokens[index + 1].children or []))
                anchor, suffix = slug, 0
                while anchor in headings:
                    suffix += 1
                    anchor = f"{slug}-{suffix}"
                headings.add(anchor)
            pending = list(token.children or [])
            while pending:
                child = pending.pop()
                pending.extend(child.children or [])
                if child.type == "link_open":
                    links.append(child.attrGet("href") or "")
                elif child.type == "image":
                    links.append(child.attrGet("src") or "")
        links_by_path[path] = links
        headings_by_path[path.resolve()] = headings

    for path, links in links_by_path.items():
        relative = path.relative_to(ROOT)
        boundary = ROOT
        if len(relative.parts) > 2 and relative.parts[0] == "skills":
            boundary = ROOT / "skills" / relative.parts[1]
        for target in links:
            url = urlsplit(target)
            if url.scheme or url.netloc:
                continue
            destination = (path.parent / unquote(url.path)).resolve() if url.path else path.resolve()
            if not destination.is_relative_to(boundary):
                errors.append(f"{relative}: link leaves distributable package: {target}")
            elif not destination.exists():
                errors.append(f"{relative}: missing link target {target}")
            elif url.fragment and destination.suffix == ".md":
                if unquote(url.fragment) not in headings_by_path.get(destination, set()):
                    errors.append(f"{relative}: missing anchor {target}")
    return len(files)


def validate_cli(skill_names: list[str], errors: list[str]) -> None:
    try:
        result = subprocess.run(
            ["npx", "--yes", "skills@1.5.26", "add", ".", "--list"],
            cwd=ROOT, capture_output=True, text=True, timeout=120,
            env={**os.environ, "DISABLE_TELEMETRY": "1", "NO_COLOR": "1"},
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        errors.append(f"skills CLI discovery failed: {exc}")
        return
    output = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", result.stdout + result.stderr)
    # The pinned CLI has no JSON mode for --list. Fail closed on an output change.
    found = re.search(r"Found (\d+) skills?\b", output)
    names = sorted(re.findall(
        r"^│ {4}([a-z0-9]+(?:-[a-z0-9]+)*)\s*$", output, re.MULTILINE
    ))
    if result.returncode or not found or int(found.group(1)) != len(skill_names) or names != sorted(skill_names):
        errors.append(
            f"skills CLI: expected {sorted(skill_names)!r}, discovered {names!r} "
            f"(exit {result.returncode})\n{output}"
        )


def validate_workflows(errors: list[str]) -> None:
    workflow_dir = ROOT / ".github" / "workflows"
    for path in sorted((*workflow_dir.glob("*.yml"), *workflow_dir.glob("*.yaml"))):
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            match = re.match(r"^\s*(?:-\s*)?uses:\s*[\"']?([^\"'\s#]+)", line)
            if not match:
                continue
            action = match.group(1)
            if action.startswith(("./", "docker://")):
                continue
            _, separator, revision = action.rpartition("@")
            if not separator or not ACTION_SHA_RE.fullmatch(revision):
                errors.append(
                    f"{path.relative_to(ROOT)}:{line_number}: action must use a full commit SHA"
                )


def validate_manifests(skill_names: list[str], errors: list[str]) -> None:
    metadata_path = ROOT / "skills.sh.json"
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"skills.sh.json: {exc}")
    else:
        listed = sorted(
            skill
            for grouping in metadata.get("groupings", [])
            for skill in grouping.get("skills", [])
        )
        if listed != skill_names:
            errors.append(
                f"skills.sh.json: listed skills {listed!r} do not match discovered skills {skill_names!r}"
            )

    plugin_path = ROOT / ".codex-plugin" / "plugin.json"
    try:
        plugin = json.loads(plugin_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f".codex-plugin/plugin.json: {exc}")
        plugin = {}
    else:
        if plugin.get("name") != "kovaa-agent-skills":
            errors.append(".codex-plugin/plugin.json: unexpected plugin name")
        if plugin.get("skills") != "./skills/":
            errors.append(".codex-plugin/plugin.json: skills must point to ./skills/")
        if plugin.get("author", {}).get("name") != "kovaa":
            errors.append(".codex-plugin/plugin.json: author name must be kovaa")
        if plugin.get("interface", {}).get("developerName") != "kovaa":
            errors.append(".codex-plugin/plugin.json: developer name must be kovaa")
        if not SEMVER_RE.fullmatch(str(plugin.get("version", ""))):
            errors.append(".codex-plugin/plugin.json: version must be SemVer")

    marketplace_path = ROOT / ".agents" / "plugins" / "marketplace.json"
    try:
        marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f".agents/plugins/marketplace.json: {exc}")
    else:
        plugins = marketplace.get("plugins", [])
        if marketplace.get("name") != "kovaa":
            errors.append(".agents/plugins/marketplace.json: marketplace name must be kovaa")
        if len(plugins) != 1 or plugins[0].get("name") != "kovaa-agent-skills":
            errors.append(".agents/plugins/marketplace.json: expected one kovaa-agent-skills entry")
        elif plugins[0].get("source") != {"source": "local", "path": "."}:
            errors.append(".agents/plugins/marketplace.json: plugin source must be local path .")

    claude_plugin_path = ROOT / ".claude-plugin" / "plugin.json"
    try:
        claude_plugin = json.loads(claude_plugin_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f".claude-plugin/plugin.json: {exc}")
        claude_plugin = {}
    else:
        if claude_plugin.get("name") != "kovaa-agent-skills":
            errors.append(".claude-plugin/plugin.json: unexpected plugin name")
        if claude_plugin.get("author", {}).get("name") != "kovaa":
            errors.append(".claude-plugin/plugin.json: author name must be kovaa")
        if not SEMVER_RE.fullmatch(str(claude_plugin.get("version", ""))):
            errors.append(".claude-plugin/plugin.json: version must be SemVer")
        if plugin and claude_plugin.get("version") != plugin.get("version"):
            errors.append("Codex and Claude plugin versions must match")

    claude_marketplace_path = ROOT / ".claude-plugin" / "marketplace.json"
    try:
        claude_marketplace = json.loads(claude_marketplace_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f".claude-plugin/marketplace.json: {exc}")
        claude_marketplace = {}
    else:
        plugins = claude_marketplace.get("plugins", [])
        if claude_marketplace.get("name") != "kovaa":
            errors.append(".claude-plugin/marketplace.json: marketplace name must be kovaa")
        if len(plugins) != 1 or plugins[0].get("name") != "kovaa-agent-skills":
            errors.append(".claude-plugin/marketplace.json: expected one kovaa-agent-skills entry")
        else:
            if plugins[0].get("source") != "./":
                errors.append(".claude-plugin/marketplace.json: plugin source must be ./")
            if not SEMVER_RE.fullmatch(str(plugins[0].get("version", ""))):
                errors.append(".claude-plugin/marketplace.json: plugin version must be SemVer")

    release_manifest_path = ROOT / ".release-please-manifest.json"
    try:
        release_manifest = json.loads(release_manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f".release-please-manifest.json: {exc}")
        release_manifest = {}
    release_version = str(release_manifest.get(".", ""))
    if not SEMVER_RE.fullmatch(release_version):
        errors.append(".release-please-manifest.json: root version must be SemVer")
    claude_marketplace_plugins = claude_marketplace.get("plugins", [])
    claude_marketplace_version = (
        claude_marketplace_plugins[0].get("version")
        if len(claude_marketplace_plugins) == 1
        else None
    )
    for manifest_name, manifest_version in (
        (".codex-plugin/plugin.json", plugin.get("version")),
        (".claude-plugin/plugin.json", claude_plugin.get("version")),
        (".claude-plugin/marketplace.json", claude_marketplace_version),
    ):
        if release_version and manifest_version != release_version:
            errors.append(f"{manifest_name}: version must match the release manifest")

    release_config_path = ROOT / "release-please-config.json"
    try:
        release_config = json.loads(release_config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"release-please-config.json: {exc}")
    else:
        package = release_config.get("packages", {}).get(".", {})
        if package.get("release-type") != "simple":
            errors.append("release-please-config.json: root release type must be simple")
        expected_json_files = {
            (".codex-plugin/plugin.json", "$.version"),
            (".claude-plugin/plugin.json", "$.version"),
            (".claude-plugin/marketplace.json", "$.plugins[0].version"),
        }
        configured_json_files = {
            (item.get("path"), item.get("jsonpath"))
            for item in package.get("extra-files", [])
            if isinstance(item, dict) and item.get("type") == "json"
        }
        if configured_json_files != expected_json_files:
            errors.append("release-please-config.json: managed JSON version files are incomplete")
        expected_readme_files = {
            "README.md",
            "skills/doc-research/README.md",
            "skills/dev-docs/README.md",
            "skills/dev-rules/README.md",
        }
        configured_readme_files = {
            item for item in package.get("extra-files", []) if isinstance(item, str)
        }
        if configured_readme_files != expected_readme_files:
            errors.append("release-please-config.json: managed README version files are incomplete")

    for readme_path in (
        ROOT / "README.md",
        ROOT / "skills" / "doc-research" / "README.md",
        ROOT / "skills" / "dev-docs" / "README.md",
        ROOT / "skills" / "dev-rules" / "README.md",
    ):
        marker_lines = [
            line
            for line in readme_path.read_text(encoding="utf-8").splitlines()
            if "x-release-please-version" in line
        ]
        if len(marker_lines) != 1:
            errors.append(
                f"{readme_path.relative_to(ROOT)}: expected one release-please version marker, found {len(marker_lines)}"
            )
            continue
        version_match = re.search(r"`v([^`]+)`.*x-release-please-version", marker_lines[0])
        readme_version = version_match.group(1) if version_match else ""
        if not SEMVER_RE.fullmatch(readme_version):
            errors.append(f"{readme_path.relative_to(ROOT)}: marker line must contain a SemVer `vX.Y.Z`")
        elif release_version and readme_version != release_version:
            errors.append(f"{readme_path.relative_to(ROOT)}: version must match the release manifest")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-cli", action="store_true", help="also verify exact discovery with skills@1.5.26")
    args = parser.parse_args()
    errors: list[str] = []
    for required in (
        "README.md",
        "LICENSE",
        "CHANGELOG.md",
        "CONTRIBUTING.md",
        "SECURITY.md",
        "PRIVACY.md",
        ".release-please-manifest.json",
        "release-please-config.json",
    ):
        if not (ROOT / required).is_file():
            errors.append(f"{required}: required repository file is missing")

    skill_names = validate_skills(errors)
    markdown_count = validate_markdown(errors)
    validate_workflows(errors)
    validate_manifests(skill_names, errors)
    if args.check_cli and not errors:
        validate_cli(skill_names, errors)

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"Validated {len(skill_names)} skills and {markdown_count} Markdown files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
