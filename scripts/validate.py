#!/usr/bin/env python3
"""Validate the distributable Agent Skills repository without third-party packages."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote

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
LINK_RE = re.compile(r"(?<!!)\[[^]]*\]\(([^)]+)\)")
HEADING_RE = re.compile(r"^#{1,6}\s+(.+?)\s*#*$")
FENCE_RE = re.compile(r"^\s*(```+|~~~+)")


class ValidationError(Exception):
    """Raised when one or more repository checks fail."""


def github_slug(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value)
    value = re.sub(r"[`*_~]", "", value).strip().lower()
    value = re.sub(r"[^\w\- ]", "", value, flags=re.UNICODE)
    return value.replace(" ", "-")


def visible_markdown_lines(text: str, path: Path, errors: list[str]) -> list[str]:
    visible: list[str] = []
    fence_char: str | None = None
    for line in text.splitlines():
        match = FENCE_RE.match(line)
        if match:
            marker = match.group(1)[0]
            if fence_char is None:
                fence_char = marker
            elif fence_char == marker:
                fence_char = None
            continue
        if fence_char is None:
            visible.append(line)
    if fence_char is not None:
        errors.append(f"{path.relative_to(ROOT)}: unclosed fenced block")
    return visible


def parse_frontmatter(path: Path, errors: list[str]) -> tuple[str, str]:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        errors.append(f"{path.relative_to(ROOT)}: missing YAML frontmatter")
        return "", ""

    block = match.group(1)
    name_match = re.search(r"^name:\s*(\S+)\s*$", block, re.MULTILINE)
    description_match = re.search(
        r"^description:\s*(?:>-\s*\n((?:[ \t]+.*(?:\n|$))+)|([^\n]+))",
        block,
        re.MULTILINE,
    )
    if not name_match:
        errors.append(f"{path.relative_to(ROOT)}: missing frontmatter name")
    if not description_match:
        errors.append(f"{path.relative_to(ROOT)}: missing frontmatter description")

    name = name_match.group(1) if name_match else ""
    if description_match:
        raw_description = description_match.group(1) or description_match.group(2) or ""
        description = " ".join(line.strip() for line in raw_description.splitlines()).strip()
    else:
        description = ""
    return name, description


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
    return sorted(name for name in names if name)


def validate_markdown(errors: list[str]) -> None:
    markdown_files = sorted(ROOT.rglob("*.md"))
    visible_by_path: dict[Path, list[str]] = {}
    headings_by_path: dict[Path, set[str]] = {}

    for path in markdown_files:
        text = path.read_text(encoding="utf-8")
        relative = path.relative_to(ROOT)
        if CYRILLIC_RE.search(text):
            errors.append(f"{relative}: Cyrillic text remains")
        local_path = LOCAL_PATH_RE.search(text)
        if local_path:
            errors.append(f"{relative}: machine-local absolute path {local_path.group(0)!r}")
        visible = visible_markdown_lines(text, path, errors)
        visible_by_path[path.resolve()] = visible
        headings_by_path[path.resolve()] = {
            github_slug(match.group(1))
            for line in visible
            if (match := HEADING_RE.match(line))
        }

    for resolved_path, lines in visible_by_path.items():
        path = Path(resolved_path)
        for line in lines:
            for raw_target in LINK_RE.findall(line):
                target = raw_target.strip().split()[0]
                if target.startswith(("http://", "https://", "mailto:", "<")):
                    continue
                target = unquote(target.strip("<>"))
                path_part, _, fragment = target.partition("#")
                destination = (path.parent / path_part).resolve() if path_part else path.resolve()
                if not destination.exists():
                    errors.append(f"{path.relative_to(ROOT)}: missing link target {target}")
                elif fragment and destination.suffix == ".md":
                    if fragment not in headings_by_path.get(destination, set()):
                        errors.append(f"{path.relative_to(ROOT)}: missing anchor {target}")


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
    validate_markdown(errors)
    validate_manifests(skill_names, errors)

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"Validated {len(skill_names)} skills and {len(list(ROOT.rglob('*.md')))} Markdown files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
