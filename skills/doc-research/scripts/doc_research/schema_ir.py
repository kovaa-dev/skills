from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import shutil
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Iterator
from xml.parsers import expat


XSD_NAMESPACE = "http://www.w3.org/2001/XMLSchema"
SCHEMATRON_NAMESPACE = "http://purl.oclc.org/dsdl/schematron"
# Bump whenever persisted records or model-facing fact semantics change.
SCHEMA_IR_VERSION = 2
MAX_SCHEMA_BLOCKS = 64
MAX_SCHEMA_CHARS = 16 * 1024 * 1024
MAX_SCHEMA_NODES = 200_000
MAX_SCHEMA_DEPTH = 256
MAX_NODE_TEXT = 8_000
MAX_NODE_ATTRIBUTES = 256
MAX_ATTRIBUTE_CHARS = 32_000
MAX_ATTRIBUTE_VALUE_CHARS = 8_000
MAX_SCHEMA_PATH_CHARS = 16_000

FENCE_OPEN = re.compile(r"^\s*(`{3,}|~{3,})\s*(xml|xsd)\s*$", re.IGNORECASE)
HEADING = re.compile(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$")
SCHEMA_NAME = re.compile(r"`([^`]+\.(?:xsd|xml))`", re.IGNORECASE)
XML_ENCODING = re.compile(
    br"^\s*<\?xml\s+[^>]*encoding\s*=\s*['\"]([A-Za-z0-9._-]+)['\"]",
    re.IGNORECASE,
)


@dataclass
class XmlNode:
    qname: str
    attrs: dict[str, str]
    line: int
    parent: XmlNode | None = None
    children: list[XmlNode] = field(default_factory=list)
    text_parts: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SchemaRecord:
    record_order: int
    parent_order: int | None
    namespace: str
    kind: str
    name: str | None
    path: str
    source_line: int
    attributes_json: str
    text: str | None
    documentation: str | None
    fact_text: str


@dataclass(frozen=True)
class SchemaBlock:
    block_index: int
    schema_name: str
    block_hash: str
    markdown_start_line: int
    markdown_end_line: int
    target_namespace: str | None
    records: tuple[SchemaRecord, ...]


@dataclass(frozen=True)
class NormalizedSchemaSource:
    narrative_text: str
    blocks: tuple[SchemaBlock, ...]
    parsed_blocks: int = 0
    reused_blocks: int = 0
    warnings: tuple[str, ...] = ()


def split_qname(value: str) -> tuple[str, str]:
    if "}" in value:
        return tuple(value.split("}", 1))  # type: ignore[return-value]
    return "", value


def local_name(value: str) -> str:
    return split_qname(value)[1]


def compact_text(value: str, limit: int = MAX_NODE_TEXT) -> str:
    normalized = " ".join(value.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 1].rstrip() + "…"


def node_text(node: XmlNode) -> str:
    pieces = list(node.text_parts)
    for child in node.children:
        pieces.append(node_text(child))
    return compact_text(" ".join(pieces))


def direct_documentation(node: XmlNode) -> str | None:
    values: list[str] = []
    for child in node.children:
        namespace, kind = split_qname(child.qname)
        if namespace == XSD_NAMESPACE and kind == "annotation":
            for item in child.children:
                item_namespace, item_kind = split_qname(item.qname)
                if item_namespace == XSD_NAMESPACE and item_kind == "documentation":
                    value = node_text(item)
                    if value:
                        values.append(value)
    if not values:
        return None
    return compact_text(" | ".join(values))


def parse_xml_tree(xml_text: str, location: str) -> XmlNode:
    if len(xml_text) > MAX_SCHEMA_CHARS:
        raise ValueError(
            f"{location}: XSD block exceeds {MAX_SCHEMA_CHARS} characters"
        )

    parser = expat.ParserCreate(namespace_separator="}")
    parser.buffer_text = True
    parser.SetParamEntityParsing(expat.XML_PARAM_ENTITY_PARSING_NEVER)
    stack: list[XmlNode] = []
    root: XmlNode | None = None
    node_count = 0

    def start(name: str, attrs: dict[str, str]) -> None:
        nonlocal root, node_count
        node_count += 1
        if node_count > MAX_SCHEMA_NODES:
            raise ValueError(f"{location}: XSD exceeds {MAX_SCHEMA_NODES} nodes")
        if len(stack) >= MAX_SCHEMA_DEPTH:
            raise ValueError(f"{location}: XSD exceeds nesting depth {MAX_SCHEMA_DEPTH}")
        if len(attrs) > MAX_NODE_ATTRIBUTES:
            raise ValueError(
                f"{location}:{parser.CurrentLineNumber}: XSD node exceeds "
                f"{MAX_NODE_ATTRIBUTES} attributes"
            )
        attribute_chars = sum(len(key) + len(value) for key, value in attrs.items())
        if attribute_chars > MAX_ATTRIBUTE_CHARS or any(
            len(value) > MAX_ATTRIBUTE_VALUE_CHARS for value in attrs.values()
        ):
            raise ValueError(
                f"{location}:{parser.CurrentLineNumber}: XSD attributes exceed safe limits"
            )
        node = XmlNode(name, dict(attrs), parser.CurrentLineNumber)
        if stack:
            node.parent = stack[-1]
            stack[-1].children.append(node)
        else:
            root = node
        stack.append(node)

    def end(_name: str) -> None:
        stack.pop()

    def characters(value: str) -> None:
        if stack and value:
            stack[-1].text_parts.append(value)

    def reject_doctype(*_args: object) -> None:
        raise ValueError(f"{location}: DTD declarations are not allowed in XSD input")

    parser.StartElementHandler = start
    parser.EndElementHandler = end
    parser.CharacterDataHandler = characters
    parser.StartDoctypeDeclHandler = reject_doctype
    parser.ExternalEntityRefHandler = lambda *_args: 0
    try:
        parser.Parse(xml_text, True)
    except ValueError:
        raise
    except expat.ExpatError as exc:
        raise ValueError(f"{location}:{exc.lineno}: invalid XML: {exc}") from exc

    if root is None:
        raise ValueError(f"{location}: empty XML input")
    return root


def looks_like_xsd(xml_text: str) -> bool:
    head = xml_text[:16_384]
    return bool(
        re.search(r"<(?:[A-Za-z_][\w.-]*:)?schema(?:\s|>)", head)
        and XSD_NAMESPACE in head
    )


def occurrence(node: XmlNode) -> tuple[str, str]:
    return node.attrs.get("minOccurs", "1"), node.attrs.get("maxOccurs", "1")


def presence_for(node: XmlNode) -> str:
    _namespace, kind = split_qname(node.qname)
    if kind == "attribute":
        use = node.attrs.get("use", "optional")
        if use == "prohibited":
            return "prohibited"
        if use != "required":
            return "optional"
    minimum, _maximum = occurrence(node)
    if minimum == "0":
        return "optional"
    ancestor = node.parent
    while ancestor is not None:
        namespace, kind = split_qname(ancestor.qname)
        if namespace == XSD_NAMESPACE and kind == "choice":
            return "conditional"
        if namespace == XSD_NAMESPACE and ancestor.attrs.get("minOccurs") == "0":
            return "conditional"
        ancestor = ancestor.parent
    return "required"


def component_segment(node: XmlNode, kind: str, sibling_index: int) -> str:
    if kind == "attribute":
        value = node.attrs.get("name") or node.attrs.get("ref")
        return f"@{value}" if value else f"@attribute[{sibling_index}]"
    if kind == "element":
        return node.attrs.get("name") or node.attrs.get("ref") or f"element[{sibling_index}]"
    if kind in {"complexType", "simpleType", "group", "attributeGroup"}:
        value = node.attrs.get("name") or node.attrs.get("ref")
        return f"{kind}:{value}" if value else f"{kind}[{sibling_index}]"
    return f"{kind}[{sibling_index}]"


def fact_for(
    node: XmlNode,
    namespace: str,
    kind: str,
    path: str,
    documentation: str | None,
) -> str:
    prefix = "XSD" if namespace == XSD_NAMESPACE else (
        "Schematron" if namespace == SCHEMATRON_NAMESPACE else f"XML {{{namespace}}}"
    )
    parts = [prefix, kind]
    name = node.attrs.get("name") or node.attrs.get("ref")
    if name:
        parts.append(name)
    if path:
        parts.append(f"path={path}")
    if kind in {"element", "attribute", "sequence", "choice", "all", "group"}:
        minimum, maximum = occurrence(node)
        parts.extend((f"minOccurs={minimum}", f"maxOccurs={maximum}"))
    if kind in {"element", "attribute"}:
        parts.append(f"presence={presence_for(node)}")
        parts.append("presence_scope=local-parent-and-type-use")
    for key in (
        "type",
        "base",
        "value",
        "use",
        "form",
        "context",
        "test",
        "code",
        "path",
        "refer",
        "xpath",
        "targetNamespace",
        "elementFormDefault",
        "attributeFormDefault",
    ):
        if key in node.attrs:
            parts.append(f"{key}={node.attrs[key]}")
    if documentation:
        parts.append(f"documentation={documentation}")
    elif namespace == SCHEMATRON_NAMESPACE and kind in {"assert", "report"}:
        message = node_text(node)
        if message:
            parts.append(f"message={message}")
    return compact_text(" ".join(parts), 12_000)


def records_from_root(root: XmlNode, location: str) -> tuple[str | None, tuple[SchemaRecord, ...]]:
    root_namespace, root_kind = split_qname(root.qname)
    if root_namespace != XSD_NAMESPACE or root_kind != "schema":
        raise ValueError(f"{location}: XML root is not an XML Schema schema element")

    records: list[SchemaRecord] = []
    orders: dict[int, int] = {}

    def visit(node: XmlNode, parent_path: str, sibling_index: int) -> None:
        namespace, kind = split_qname(node.qname)
        segment = component_segment(node, kind, sibling_index)
        structural = namespace == XSD_NAMESPACE and kind in {
            "element",
            "attribute",
            "complexType",
            "simpleType",
            "group",
            "attributeGroup",
        }
        path = f"{parent_path}/{segment}" if structural else parent_path
        if not path:
            path = "/schema"
        if len(path) > MAX_SCHEMA_PATH_CHARS:
            raise ValueError(f"{location}:{node.line}: normalized XSD path is too long")
        documentation = direct_documentation(node)
        text = None
        if kind in {"documentation", "assert", "report", "error"}:
            text = node_text(node) or None
        order = len(records) + 1
        orders[id(node)] = order
        parent_order = orders.get(id(node.parent)) if node.parent is not None else None
        fact = fact_for(node, namespace, kind, path, documentation)
        records.append(
            SchemaRecord(
                record_order=order,
                parent_order=parent_order,
                namespace=namespace,
                kind=kind,
                name=node.attrs.get("name") or node.attrs.get("ref"),
                path=path,
                source_line=node.line,
                attributes_json=json.dumps(
                    node.attrs, ensure_ascii=False, sort_keys=True, separators=(",", ":")
                ),
                text=text,
                documentation=documentation,
                fact_text=fact,
            )
        )
        counters: dict[str, int] = {}
        for child in node.children:
            child_kind = local_name(child.qname)
            counters[child_kind] = counters.get(child_kind, 0) + 1
            visit(child, path, counters[child_kind])

    visit(root, "", 1)
    return root.attrs.get("targetNamespace"), tuple(records)


def normalize_block(
    xml_text: str,
    *,
    block_index: int,
    schema_name: str,
    markdown_start_line: int,
    markdown_end_line: int,
    location: str,
) -> SchemaBlock:
    root = parse_xml_tree(xml_text, location)
    target_namespace, records = records_from_root(root, location)
    return SchemaBlock(
        block_index=block_index,
        schema_name=schema_name,
        block_hash=hashlib.sha256(xml_text.encode("utf-8")).hexdigest(),
        markdown_start_line=markdown_start_line,
        markdown_end_line=markdown_end_line,
        target_namespace=target_namespace,
        records=records,
    )


def schema_name_from_heading(heading: str | None, block_index: int) -> str:
    if heading:
        matched = SCHEMA_NAME.search(heading)
        if matched:
            return matched.group(1)
    return f"embedded-schema-{block_index}.xsd"


def normalize_markdown(
    raw: str,
    source_name: str,
    cached_blocks: dict[str, SchemaBlock] | None = None,
) -> NormalizedSchemaSource:
    lines = raw.splitlines(keepends=True)
    output: list[str] = []
    blocks: list[SchemaBlock] = []
    parsed_blocks = 0
    reused_blocks = 0
    warnings: list[str] = []
    encountered_blocks = 0
    latest_heading: str | None = None
    index = 0

    while index < len(lines):
        line_without_newline = lines[index].rstrip("\r\n")
        heading = HEADING.match(line_without_newline)
        if heading:
            latest_heading = heading.group(1).strip()
        opening = FENCE_OPEN.match(line_without_newline)
        if not opening:
            output.append(lines[index])
            index += 1
            continue

        fence = opening.group(1)
        fence_char = re.escape(fence[0])
        closing = re.compile(rf"^\s*{fence_char}{{{len(fence)},}}\s*$")
        end = index + 1
        while end < len(lines) and not closing.match(lines[end].rstrip("\r\n")):
            end += 1
        if end >= len(lines):
            output.append(lines[index])
            index += 1
            continue

        xml_text = "".join(lines[index + 1 : end])
        if not looks_like_xsd(xml_text):
            output.extend(lines[index : end + 1])
            index = end + 1
            continue
        if encountered_blocks >= MAX_SCHEMA_BLOCKS:
            raise ValueError(f"{source_name}: more than {MAX_SCHEMA_BLOCKS} XSD blocks")
        encountered_blocks += 1
        block_index = encountered_blocks
        schema_name = schema_name_from_heading(latest_heading, block_index)
        block_hash = hashlib.sha256(xml_text.encode("utf-8")).hexdigest()
        cached = (cached_blocks or {}).get(block_hash)
        if cached is not None:
            block = replace(
                cached,
                block_index=block_index,
                schema_name=schema_name,
                markdown_start_line=index + 2,
                markdown_end_line=end,
            )
            reused_blocks += 1
        else:
            try:
                block = normalize_block(
                    xml_text,
                    block_index=block_index,
                    schema_name=schema_name,
                    markdown_start_line=index + 2,
                    markdown_end_line=end,
                    location=f"{source_name}:XSD block {block_index}",
                )
            except ValueError as error:
                # A broken/untrusted embedded schema must not suppress independent
                # prose. Do not parse it again as XML or call its absence coverage.
                warning = f"{source_name}: skipped XSD block {block_index} at lines {index + 2}-{end}: {error}"
                warnings.append(warning[:1000])
                output.append(f"[Schema coverage incomplete: block {block_index} could not be normalized.]\n")
                output.extend("\n" for _ in range(end - index))
                index = end + 1
                continue
            parsed_blocks += 1
        blocks.append(block)
        output.append(
            f"XSD schema {schema_name} normalized into {len(block.records)} semantic records "
            f"(Markdown lines {block.markdown_start_line}-{block.markdown_end_line}).\n"
        )
        # Keep later narrative locators aligned with the original Markdown after
        # replacing the fenced schema with one compact searchable line.
        output.extend("\n" for _ in range(end - index))
        index = end + 1

    return NormalizedSchemaSource(
        "".join(output), tuple(blocks), parsed_blocks, reused_blocks, tuple(warnings)
    )


def normalize_xsd_file(
    raw: str,
    source_name: str,
    cached_blocks: dict[str, SchemaBlock] | None = None,
) -> NormalizedSchemaSource:
    block_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    cached = (cached_blocks or {}).get(block_hash)
    if cached is not None:
        block = replace(
            cached,
            block_index=1,
            schema_name=Path(source_name).name,
            markdown_start_line=1,
            markdown_end_line=max(1, len(raw.splitlines())),
        )
        return NormalizedSchemaSource("", (block,), 0, 1)
    block = normalize_block(
        raw,
        block_index=1,
        schema_name=Path(source_name).name,
        markdown_start_line=1,
        markdown_end_line=max(1, len(raw.splitlines())),
        location=source_name,
    )
    return NormalizedSchemaSource("", (block,), 1, 0)


def normalize_schema_source(
    path: Path,
    source_name: str,
    cached_blocks: dict[str, SchemaBlock] | None = None,
) -> NormalizedSchemaSource:
    if path.suffix.lower() == ".xsd":
        raw_bytes = path.read_bytes()
        matched = XML_ENCODING.search(raw_bytes[:512])
        encoding = matched.group(1).decode("ascii") if matched else "utf-8"
        try:
            raw = raw_bytes.decode(encoding)
        except (LookupError, UnicodeDecodeError) as exc:
            raise ValueError(
                f"{source_name}: cannot decode XSD using declared encoding {encoding}"
            ) from exc
        return normalize_xsd_file(raw, source_name, cached_blocks)
    raw = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".md":
        return normalize_markdown(raw, source_name, cached_blocks)
    return NormalizedSchemaSource(raw, ())


def iter_fact_groups(block: SchemaBlock, max_chars: int) -> Iterator[str]:
    header = (
        f"Schema {block.schema_name}; block_sha256={block.block_hash}; "
        f"markdown_lines={block.markdown_start_line}-{block.markdown_end_line}"
    )
    pending: list[str] = []
    pending_length = len(header)
    for record in block.records:
        if record.kind in {"annotation", "appinfo", "documentation", "value-of"}:
            continue
        if (
            record.kind in {"complexType", "simpleType", "sequence", "all"}
            and record.name is None
            and record.attributes_json == "{}"
        ):
            continue
        locator = (
            f"[schema={block.schema_name}; xsd_line={record.source_line}; "
            f"md_line={block.markdown_start_line + record.source_line - 1}]"
        )
        line = f"{locator} {record.fact_text}"
        projected = pending_length + len(line) + 1
        if pending and projected > max_chars:
            yield header + "\n" + "\n".join(pending)
            pending = []
            pending_length = len(header)
        if len(line) + len(header) + 1 > max_chars:
            available = max(1, max_chars - len(header) - 2)
            line = line[:available].rstrip() + "…"
        pending.append(line)
        pending_length += len(line) + 1
    if pending:
        yield header + "\n" + "\n".join(pending)


def optional_capabilities() -> dict[str, object]:
    return {
        "builtin_normalizer": True,
        "xmllint": shutil.which("xmllint") is not None,
        "python_xmlschema": importlib.util.find_spec("xmlschema") is not None,
    }
