from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import platform
import re
import shutil
import tempfile
from contextlib import closing, contextmanager
from pathlib import Path
from typing import Iterable, Iterator


try:
    import sqlite3
except ImportError as exc:  # Some minimal Python builds omit the stdlib extension.
    sqlite3 = None  # type: ignore[assignment]
    SQLITE_IMPORT_ERROR: str | None = str(exc)
else:
    SQLITE_IMPORT_ERROR = None

SUPPORTED_SUFFIXES = {".md", ".txt", ".jsonl"}

MIN_PYTHON = (3, 10)

APPLICATION_ID = 0x44524348  # "DRCH"

SCHEMA_VERSION = 1

RESEARCH_APPLICATION_ID = 0x44525348  # "DRSH"

RESEARCH_SCHEMA_VERSION = 1

RECEIPT_APPLICATION_ID = 0x44524350  # "DRCP"

RECEIPT_SCHEMA_VERSION = 1

CATALOG_APPLICATION_ID = 0x44524354  # "DRCT"

CATALOG_SCHEMA_VERSION = 1

DEFAULT_MAX_SOURCE_BYTES = 256 * 1024 * 1024

DEFAULT_MAX_CORPUS_BYTES = 8 * 1024 * 1024 * 1024

DEFAULT_MAX_COMPARE_UNITS = 100_000

MIN_INDEX_HEADROOM_BYTES = 16 * 1024 * 1024

MAX_RESEARCH_TEXT = 4_000

MAX_RESEARCH_EXCERPT = 2_000

MAX_RESEARCH_JSON = 16_000

MAX_BATCH_QUERIES = 8

MAX_BATCH_RECORDS = 100

MAX_BATCH_INPUT_BYTES = 256 * 1024

MAX_QUERY_TEXT = 2_000

MAX_FILTER_TEXT = 1_000

MAX_CATALOG_CORPORA = 16

MAX_CATALOG_PROJECTS = 8

DEFAULT_MAX_ARCHIVE_ENTRIES = 10_000

DEFAULT_MAX_ARCHIVE_BYTES = 8 * 1024 * 1024 * 1024

DEFAULT_MAX_ARCHIVE_MEMBER_BYTES = 256 * 1024 * 1024

DEFAULT_MAX_ARCHIVE_RATIO = 200

METADATA_COLUMNS = ("key", "value")

INDEX_FINGERPRINT_KEY = "index_fingerprint"

SOURCE_COLUMNS = ("path", "sha256", "indexed_at", "chunk_count")

CHUNK_COLUMNS = (
    "source_path",
    "source",
    "source_hash",
    "page",
    "section",
    "version",
    "date",
    "context",
    "text",
)

PAGE_MARKER = re.compile(r"^\s*<!--\s*page\s*:\s*(.+?)\s*-->\s*$", re.IGNORECASE)

HEADING = re.compile(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$")

TOKEN = re.compile(r"\w+", re.UNICODE)

SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")

RECORD_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")

FACET_STATUSES = {"open", "supported", "refuted", "conflicted", "unresolved", "out-of-scope"}

RESEARCH_STATUSES = {"active", "complete"}

CONFLICT_STATUSES = {"open", "resolved"}

GAP_STATUSES = {"open", "resolved", "out-of-scope"}

CONFIDENCE_VALUES = {"confirmed", "probable", "uncertain"}

CATALOG_ADAPTERS = {"local-index", "external"}

PROJECT_ANCHOR_KINDS = {"connector", "filesystem", "manual"}

if sqlite3 is None:
    SQLITE_OPERATIONAL_ERROR = RuntimeError
    HANDLED_ERRORS = (OSError, ValueError, RuntimeError)
else:
    SQLITE_OPERATIONAL_ERROR = sqlite3.OperationalError
    HANDLED_ERRORS = (OSError, ValueError, RuntimeError, sqlite3.Error)

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def normalize_text(text: str) -> str:
    return "\n".join(" ".join(line.split()) for line in text.splitlines()).strip()

def connect(db_path: Path, *, readonly: bool = False) -> sqlite3.Connection:
    if sqlite3 is None:
        raise RuntimeError(f"Python sqlite3 module is unavailable: {SQLITE_IMPORT_ERROR}")
    if readonly:
        connection = sqlite3.connect(f"{db_path.resolve().as_uri()}?mode=ro", uri=True)
    else:
        connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA trusted_schema = OFF")
    if readonly:
        connection.execute("PRAGMA query_only = ON")
    return connection

@contextmanager
def database(db_path: Path, *, readonly: bool = False) -> Iterator[sqlite3.Connection]:
    with closing(connect(db_path, readonly=readonly)) as connection:
        with connection:
            yield connection

def table_exists(connection: sqlite3.Connection, table: str) -> bool:
    return (
        connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
            (table,),
        ).fetchone()
        is not None
    )

def schema_version(connection: sqlite3.Connection) -> int:
    return int(connection.execute("PRAGMA user_version").fetchone()[0])

def application_id(connection: sqlite3.Connection) -> int:
    return int(connection.execute("PRAGMA application_id").fetchone()[0])

def database_objects(connection: sqlite3.Connection) -> set[str]:
    return {
        str(row["name"])
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'"
        )
    }

def file_signature(path: Path) -> tuple[int, int, int, int]:
    status = path.stat()
    return (status.st_dev, status.st_ino, status.st_size, status.st_mtime_ns)

def harden_database_permissions(db_path: Path) -> bool:
    if os.name == "nt":
        return False
    current = db_path.stat().st_mode & 0o777
    if current == 0o600:
        return False
    db_path.chmod(0o600)
    return True

def table_columns(connection: sqlite3.Connection, table: str) -> tuple[str, ...]:
    return tuple(row["name"] for row in connection.execute(f"PRAGMA table_info({table})"))

def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()

def validate_record_id(value: str, field: str) -> str:
    normalized = value.strip()
    if not RECORD_ID.fullmatch(normalized):
        raise ValueError(
            f"{field} must be 1-128 characters using letters, digits, dot, "
            "underscore, colon, or hyphen"
        )
    return normalized

def required_record_id(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} is required")
    return validate_record_id(value, field)

def required_research_text(value: object, field: str, limit: int = MAX_RESEARCH_TEXT) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} is required")
    normalized = value.strip()
    if len(normalized) > limit:
        raise ValueError(f"{field} exceeds {limit} characters")
    return normalized

def optional_research_text(
    value: object, field: str, limit: int = MAX_RESEARCH_TEXT
) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field} must be text")
    normalized = value.strip()
    if not normalized:
        return None
    if len(normalized) > limit:
        raise ValueError(f"{field} exceeds {limit} characters")
    return normalized

def load_bounded_json(path: Path, label: str) -> object:
    resolved = path.resolve()
    if not resolved.is_file():
        raise ValueError(f"{label} does not exist: {resolved}")
    size = resolved.stat().st_size
    if size > MAX_BATCH_INPUT_BYTES:
        raise ValueError(
            f"{label} exceeds {MAX_BATCH_INPUT_BYTES} bytes ({size} bytes)"
        )
    try:
        return json.loads(resolved.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} is invalid JSON: {exc}") from exc

def emit_json(payload: object, pretty: bool = False) -> None:
    options: dict[str, object] = {"ensure_ascii": False}
    if pretty:
        options["indent"] = 2
    else:
        options["separators"] = (",", ":")
    print(json.dumps(payload, **options))

def clip_text(value: str, limit: int) -> tuple[str, bool]:
    if len(value) <= limit:
        return value, False
    if limit == 1:
        return "…", True
    return value[: limit - 1].rstrip() + "…", True

def join_bounded(lines: Iterable[str], limit: int) -> tuple[str, bool]:
    output: list[str] = []
    used = 0
    for line in lines:
        piece = line if not output else f"\n{line}"
        remaining = limit - used
        if remaining <= 0:
            return "".join(output), True
        if len(piece) > remaining:
            clipped, _ = clip_text(piece, remaining)
            output.append(clipped)
            return "".join(output), True
        output.append(piece)
        used += len(piece)
    return "".join(output), False

def python_install_guidance() -> dict[str, str]:
    system = platform.system()
    source_url = "https://www.python.org/downloads/"
    if system == "Windows":
        if not shutil.which("winget"):
            return {
                "command": "start https://www.python.org/downloads/windows/",
                "source": "https://docs.python.org/3/using/windows.html",
            }
        return {
            "command": (
                "winget install 9NQ7512CXL7T -e "
                "--accept-package-agreements --disable-interactivity"
            ),
            "next_command": "py install default",
            "source": "https://docs.python.org/3/using/windows.html",
        }
    if system == "Darwin":
        command = (
            "brew install python"
            if shutil.which("brew")
            else "open https://www.python.org/downloads/macos/"
        )
        return {
            "command": command,
            "source": "https://www.python.org/downloads/macos/",
        }

    package_commands = (
        ("apt-get", "sudo apt-get update && sudo apt-get install -y python3"),
        ("dnf", "sudo dnf install -y python3"),
        ("yum", "sudo yum install -y python3"),
        ("zypper", "sudo zypper install -y python3"),
        ("pacman", "sudo pacman -S --needed python"),
        ("apk", "sudo apk add python3"),
        ("xbps-install", "sudo xbps-install -S python3"),
        ("nix-env", "nix-env -iA nixpkgs.python3"),
    )
    for executable, command in package_commands:
        if shutil.which(executable):
            return {"command": command, "source": source_url}
    command = (
        "xdg-open https://www.python.org/downloads/"
        if shutil.which("xdg-open")
        else "Open https://www.python.org/downloads/"
    )
    return {"command": command, "source": source_url}

def check_write_access(write_dir: Path) -> tuple[bool, str | None, Path]:
    resolved = write_dir.expanduser().resolve()
    try:
        if not resolved.is_dir():
            raise OSError(f"Not a directory: {resolved}")
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            prefix=".corpus-doctor-",
            suffix=".tmp",
            dir=resolved,
        ) as handle:
            handle.write("probe")
            handle.flush()
    except OSError as exc:
        return False, str(exc), resolved
    return True, None, resolved
