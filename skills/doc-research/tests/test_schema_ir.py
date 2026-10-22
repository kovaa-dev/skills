from __future__ import annotations

from test_support import *


SCHEMA_MARKDOWN = """# Transport format

Narrative marker outside the schema.

### XSD schema `sample.xsd`

```xml
<?xml version="1.0" encoding="windows-1251"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
           xmlns:sch="http://purl.oclc.org/dsdl/schematron">
  <xs:element name="Root">
    <xs:annotation>
      <xs:documentation>Root document</xs:documentation>
      <xs:appinfo>
        <sch:pattern name="Root validation">
          <sch:rule context="Root">
            <sch:assert test="A or B">One cargo branch is required</sch:assert>
          </sch:rule>
        </sch:pattern>
      </xs:appinfo>
    </xs:annotation>
    <xs:complexType>
      <xs:choice minOccurs="0">
        <xs:element name="A" type="xs:string"/>
        <xs:element name="B" minOccurs="0">
          <xs:simpleType>
            <xs:restriction base="xs:string">
              <xs:enumeration value="ROAD"/>
              <xs:pattern value="[A-Z]+"/>
            </xs:restriction>
          </xs:simpleType>
        </xs:element>
      </xs:choice>
      <xs:attribute name="Id" type="xs:string" use="required"/>
    </xs:complexType>
  </xs:element>
</xs:schema>
```
"""


class SchemaIrCliTest(CorpusCliTestCase):
    def test_index_replaces_raw_xsd_with_searchable_semantic_facts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "format.md"
            source.write_text(SCHEMA_MARKDOWN, encoding="utf-8")
            database = root / "index.sqlite"

            indexed = run_corpus("index", source, "--db", database)
            self.assertEqual(indexed.returncode, 0, indexed.stderr)
            payload = json.loads(indexed.stdout)
            self.assertEqual(payload["schema_blocks"], 1)
            self.assertGreater(payload["schema_records"], 10)

            info = json.loads(run_corpus("info", database).stdout)
            self.assertEqual(info["schema_version"], 3)
            self.assertEqual(info["schema_ir_version"], 2)
            self.assertEqual(info["schema_block_count"], 1)

            found = json.loads(run_corpus("search", database, "ROAD").stdout)
            self.assertEqual(found["result_count"], 1)
            text = found["results"][0]["text"]
            self.assertIn("XSD enumeration", text)
            self.assertIn("value=ROAD", text)
            self.assertNotIn("<xs:enumeration", text)

            with closing(sqlite3.connect(database)) as connection:
                stored = "\n".join(
                    row[0] for row in connection.execute("SELECT text FROM chunks")
                )
            self.assertIn("Narrative marker outside the schema", stored)
            self.assertNotIn("<xs:schema", stored)
            self.assertNotIn("<xs:element", stored)

    def test_schema_query_preserves_structure_presence_and_locators(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "format.md"
            source.write_text(SCHEMA_MARKDOWN, encoding="utf-8")
            database = root / "index.sqlite"
            self.assertEqual(run_corpus("index", source, "--db", database).returncode, 0)

            result = run_corpus(
                "schema-query",
                database,
                "A",
                "--kind",
                "element",
                "--purpose",
                "adapter-debugging",
                "--purpose-reason",
                "test-suite",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            record = next(item for item in payload["results"] if item["name"] == "A")
            self.assertIn("presence=conditional", record["fact_text"])
            self.assertEqual(record["attributes"]["type"], "xs:string")
            self.assertGreater(record["xsd_line"], 1)
            self.assertGreater(record["markdown_line"], record["xsd_line"])

            attribute = json.loads(
                run_corpus(
                    "schema-query",
                    database,
                    "Id",
                    "--kind",
                    "attribute",
                    "--purpose",
                    "adapter-debugging",
                    "--purpose-reason",
                    "test-suite",
                ).stdout
            )["results"][0]
            self.assertIn("presence=required", attribute["fact_text"])
            self.assertEqual(attribute["attributes"]["use"], "required")

    def test_unchanged_schema_reuses_index_and_changed_schema_replaces_records(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "format.md"
            source.write_text(SCHEMA_MARKDOWN, encoding="utf-8")
            database = root / "index.sqlite"
            first = json.loads(run_corpus("index", source, "--db", database).stdout)
            self.assertEqual(first["schema_blocks_parsed"], 1)
            self.assertEqual(first["schema_blocks_reused"], 0)

            warm = json.loads(run_corpus("index", source, "--db", database).stdout)
            self.assertFalse(warm["database_rebuilt"])
            self.assertEqual(warm["files_indexed"], 0)
            self.assertEqual(warm["schema_records"], first["schema_records"])
            self.assertEqual(warm["schema_blocks_parsed"], 0)
            self.assertEqual(warm["schema_blocks_reused"], 1)

            source.write_text(
                SCHEMA_MARKDOWN.replace(
                    "Narrative marker outside the schema.",
                    "Narrative marker outside the schema. Updated prose.",
                ),
                encoding="utf-8",
            )
            prose_only = json.loads(
                run_corpus("index", source, "--db", database).stdout
            )
            self.assertEqual(prose_only["schema_blocks_parsed"], 0)
            self.assertEqual(prose_only["schema_blocks_reused"], 1)

            source.write_text(
                source.read_text(encoding="utf-8").replace(
                    'value="ROAD"', 'value="RAIL"'
                ),
                encoding="utf-8",
            )
            changed = json.loads(run_corpus("index", source, "--db", database).stdout)
            self.assertEqual(changed["update_strategy"], "delta-copy")
            self.assertEqual(changed["files_indexed"], 1)
            self.assertEqual(changed["schema_blocks_parsed"], 1)
            self.assertEqual(changed["schema_blocks_reused"], 0)
            self.assertEqual(
                json.loads(run_corpus("search", database, "ROAD").stdout)["result_count"],
                0,
            )
            self.assertEqual(
                json.loads(run_corpus("search", database, "RAIL").stdout)["result_count"],
                1,
            )

    def test_embedded_doctype_is_isolated_without_parsing_entities(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "format.md"
            source.write_text(SCHEMA_MARKDOWN, encoding="utf-8")
            database = root / "index.sqlite"
            self.assertEqual(run_corpus("index", source, "--db", database).returncode, 0)

            source.write_text(
                SCHEMA_MARKDOWN.replace(
                    '<?xml version="1.0" encoding="windows-1251"?>',
                    '<?xml version="1.0"?><!DOCTYPE schema [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>',
                ),
                encoding="utf-8",
            )
            refused = run_corpus("index", source, "--db", database)
            self.assertEqual(refused.returncode, 0, refused.stderr)
            self.assertIn("DTD declarations are not allowed", refused.stdout)
            self.assertEqual(json.loads(refused.stdout)["schema_records"], 0)

            retained = json.loads(run_corpus("search", database, "ROAD").stdout)
            self.assertEqual(retained["result_count"], 0)
            standalone = root / "unsafe.xsd"
            standalone.write_text('<!DOCTYPE schema [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">&xxe;</xs:schema>', encoding="utf-8")
            blocked = run_corpus("index", standalone, "--db", root / "unsafe.sqlite")
            self.assertEqual(blocked.returncode, 2)
            self.assertIn("DTD declarations are not allowed", blocked.stderr)

    def test_normalize_command_is_bounded_and_reports_optional_tools(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "format.md"
            source.write_text(SCHEMA_MARKDOWN, encoding="utf-8")
            result = run_corpus(
                "normalize-xml-schema",
                source,
                "--include-records",
                "--limit",
                2,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["block_count"], 1)
            self.assertEqual(payload["result_count"], 2)
            self.assertTrue(payload["has_more"])
            self.assertTrue(payload["capabilities"]["builtin_normalizer"])

    def test_standalone_xsd_honors_declared_legacy_encoding(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "legacy.xsd"
            source.write_bytes(
                """<?xml version="1.0" encoding="windows-1251"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="Груз" type="xs:string"/>
</xs:schema>
""".encode("windows-1251")
            )
            database = root / "index.sqlite"
            indexed = run_corpus("index", source, "--db", database)
            self.assertEqual(indexed.returncode, 0, indexed.stderr)
            self.assertEqual(json.loads(indexed.stdout)["schema_records"], 2)
            found = json.loads(run_corpus("search", database, "Груз").stdout)
            self.assertEqual(found["result_count"], 1)
            self.assertIn("XSD element Груз", found["results"][0]["text"])


if __name__ == "__main__":
    unittest.main()
