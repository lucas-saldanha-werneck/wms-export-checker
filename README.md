# wms-export-checker

Independent demo, not affiliated with Breakmark.

A small script that reads CSV exports from a warehouse system and lists what is wrong with them before an integration goes live. I wrote it after reading a forward-deployed engineer job post that mentions onboarding clients from signature to go-live with ERP and WMS data. The first thing that usually breaks in that kind of onboarding is the data, so this checks the data.

It has no dependencies beyond the Python standard library.

## What it checks

- Missing files and missing columns
- Empty required fields
- Wrong types (integer, decimal, ISO date)
- Values below a minimum (for example quantity 0)
- Duplicate keys
- Orphan references (an inbound line that points to a SKU the SKU table does not have)
- The same SKU received in different units of measure

The expected shape of the export is described in a JSON schema file. See `examples/schema.json`.

## Run it

```
python -m wms_export_checker examples/sample_export --schema examples/schema.json --out report.md
```

The exit code is 1 when there are findings and 0 when the export is clean, so you can use it in a script.

On the sample data it prints 8 findings, including a SKU `GLV-777` that appears in an inbound line but not in the SKU table, and `TAP-050` received once in `ROLL` and once in `CASE`.

The sample CSV files are invented example data. They do not come from any company. Use `--real-data` to drop that note from the report when you check your own export.

## Run the tests

```
pip install pytest
python -m pytest -q
```

The tests run offline. The same command runs in GitHub Actions (`.github/workflows/test.yml`).

## What was tested

- The sample export produces exactly the 8 expected findings, on the expected lines.
- A clean export produces none.
- A missing file and a missing column are both reported.
- The command line writes the report file and returns exit code 1 when there are findings.

## What was not tested

- Real warehouse exports. Only the invented sample was used.
- Large files. The script loads each table fully into memory.
- Other encodings, other delimiters, or CSV files with a byte order mark.
- Any ERP, WMS or TMS API. This reads CSV files only.
- Python versions other than 3.12 (CI) and 3.15 (my machine).
