from __future__ import annotations

from test_support import *
from doc_research import schema_ir as SCHEMA_IR_MODULE


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


class SchemaTextFidelityTest(unittest.TestCase):
    def test_named_structural_batch_needs_no_index_and_keeps_parent_conditions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.md"
            source.write_text(SCHEMA_MARKDOWN, encoding="utf-8")
            result = run_corpus_raw("normalize-xml-schema", source, "--name", "A", "--name", "Id",
                                    "--name", "Missing", "--limit", "1")
            self.assertEqual(result.returncode, 0, result.stderr)
            first = json.loads(result.stdout)
            self.assertEqual(first["record_count"], 2)
            self.assertEqual(first["unmatched_names"], ["Missing"])
            self.assertEqual(first["records"][0]["name"], "A")
            self.assertIn("presence=conditional", first["records"][0]["fact_text"])
            second = run_corpus_raw("normalize-xml-schema", source, "--name", "A", "--name", "Id",
                                    "--name", "Missing", "--offset", first["next_offset"],
                                    "--source-hash", first["source_hash"])
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(json.loads(second.stdout)["records"][0]["attributes"]["use"], "required")
            self.assertEqual(list(Path(directory).iterdir()), [source])
            source.write_text(SCHEMA_MARKDOWN + "\nchanged", encoding="utf-8")
            stale = run_corpus_raw("normalize-xml-schema", source, "--name", "Id",
                                  "--source-hash", first["source_hash"])
            self.assertNotEqual(stale.returncode, 0)

    def normalize(self, content: str):
        return SCHEMA_IR_MODULE.normalize_xsd_file(
            '<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" '
            'xmlns:sch="http://purl.oclc.org/dsdl/schematron">'
            + content + '</xs:schema>',
            "fidelity.xsd",
        ).blocks[0].records

    def test_mixed_content_keeps_negation_in_source_order(self) -> None:
        records = self.normalize(
            '<xs:element name="Delivery"><xs:annotation>'
            '<xs:documentation>Delivery is <b>not</b> permitted.</xs:documentation>'
            '<xs:appinfo><sch:assert test="allowed">Delivery is '
            '<b>not <i>ever</i></b> permitted.</sch:assert></xs:appinfo>'
            '</xs:annotation></xs:element>'
        )
        element = next(record for record in records if record.kind == "element")
        assertion = next(record for record in records if record.kind == "assert")
        self.assertEqual(element.documentation, "Delivery is not permitted.")
        self.assertIn("documentation=Delivery is not permitted.", element.fact_text)
        self.assertEqual(assertion.text, "Delivery is not ever permitted.")
        self.assertIn("message=Delivery is not ever permitted.", assertion.fact_text)

    def test_whitespace_and_literals_survive_normalization(self) -> None:
        documentation = '  code: A  B\n\tkeep <b>  both  </b> spaces &amp; tabs\t '
        expected = '  code: A  B\n\tkeep   both   spaces & tabs\t '
        records = self.normalize(
            '<xs:element name="Literal"><xs:annotation>'
            '<xs:documentation xml:space="preserve">' + documentation
            + '</xs:documentation></xs:annotation></xs:element>'
            '<xs:enumeration value="A  B&#x9;C"/>'
        )
        element = next(record for record in records if record.kind == "element")
        document = next(record for record in records if record.kind == "documentation")
        enumeration = next(record for record in records if record.kind == "enumeration")
        self.assertEqual(element.documentation, expected)
        self.assertEqual(document.text, expected)
        self.assertIn("documentation=" + expected, element.fact_text)
        self.assertIn("value=A  B\tC", enumeration.fact_text)

    def test_long_documentation_retains_final_source_evidence(self) -> None:
        documentation = "prefix " * 2000 + "FINAL_POLICY_MARKER: no delivery."
        records = self.normalize(
            '<xs:element name="Long"><xs:annotation><xs:documentation>'
            + documentation
            + '</xs:documentation></xs:annotation></xs:element>'
        )
        element = next(record for record in records if record.kind == "element")
        document = next(record for record in records if record.kind == "documentation")
        self.assertEqual(document.text, documentation)
        self.assertEqual(element.documentation, documentation)
        self.assertTrue(element.fact_text.endswith(documentation))

    def test_record_expansion_limit_rejects_instead_of_truncating(self) -> None:
        with mock.patch.object(SCHEMA_IR_MODULE, "MAX_SCHEMA_RECORD_CHARS", 512):
            with self.assertRaisesRegex(ValueError, "normalized XSD records exceed"):
                self.normalize(
                    '<xs:element name="Long"><xs:annotation><xs:documentation>'
                    + "preserved text " * 25
                    + '</xs:documentation></xs:annotation></xs:element>'
                )


class SchemaIrCliTest(CorpusCliTestCase):
    def test_long_documentation_is_stored_and_tail_remains_searchable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "long.xsd"
            documentation = "  prefix  text\n\t" * 1000 + "TAILPOLICYMARKER: no delivery.  "
            source.write_text(
                '<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">'
                '<xs:element name="Long"><xs:annotation><xs:documentation>'
                + documentation
                + '</xs:documentation></xs:annotation></xs:element></xs:schema>',
                encoding="utf-8",
            )
            database = root / "index.sqlite"
            indexed = run_corpus("index", source, "--db", database)
            self.assertEqual(indexed.returncode, 0, indexed.stderr)
            with closing(sqlite3.connect(database)) as connection:
                stored = connection.execute(
                    "SELECT text FROM schema_records WHERE kind = 'documentation'"
                ).fetchone()[0]
                projected = [row[0] for row in connection.execute("SELECT text FROM chunks")]
            self.assertEqual(stored, documentation)
            self.assertGreater(len(projected), 1)
            self.assertTrue(any("TAILPOLICYMARKER: no delivery." in text for text in projected))
            found = run_corpus("search", database, "TAILPOLICYMARKER")
            self.assertEqual(found.returncode, 0, found.stderr)
            self.assertGreater(json.loads(found.stdout)["result_count"], 0)

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
            self.assertEqual(info["schema_ir_version"], 3)
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
