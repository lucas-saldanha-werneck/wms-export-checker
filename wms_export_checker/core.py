"""Core checks. Standard library only."""
from __future__ import annotations

import csv
import json
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path


def _valid(value: str, kind: str) -> bool:
    try:
        if kind == "int":
            int(value)
        elif kind == "decimal":
            Decimal(value)
        elif kind == "date":
            date.fromisoformat(value)
        elif kind != "str":
            raise ValueError(f"unknown type {kind}")
    except (ValueError, InvalidOperation):
        return False
    return True


def load_table(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or []), [
            {k: (v or "").strip() for k, v in row.items()} for row in reader
        ]


def check_export(folder: Path, schema: dict) -> list[dict]:
    """Return a list of findings: {table, row, check, message}.

    Row numbers are CSV line numbers (header is line 1).
    """
    findings: list[dict] = []
    tables: dict[str, list[dict[str, str]]] = {}

    def add(table, row, check, message):
        findings.append({"table": table, "row": row, "check": check, "message": message})

    for name, spec in schema["tables"].items():
        path = folder / f"{name}.csv"
        if not path.exists():
            add(name, None, "missing_file", f"{name}.csv not found")
            continue
        header, rows = load_table(path)
        tables[name] = rows
        columns = spec["columns"]
        missing = [c for c in columns if c not in header]
        for c in missing:
            add(name, None, "missing_column", f"column '{c}' not in header")
        seen: dict[str, int] = {}
        for i, row in enumerate(rows, start=2):
            for col, cspec in columns.items():
                if col in missing:
                    continue
                value = row.get(col, "")
                if value == "":
                    if cspec.get("required", False):
                        add(name, i, "empty_required", f"'{col}' is empty")
                elif not _valid(value, cspec["type"]):
                    add(name, i, "bad_type", f"'{col}'={value!r} is not a valid {cspec['type']}")
                elif cspec["type"] in ("int", "decimal") and cspec.get("min") is not None \
                        and Decimal(value) < Decimal(str(cspec["min"])):
                    add(name, i, "out_of_range", f"'{col}'={value} is below {cspec['min']}")
            key = spec.get("key")
            if key and key not in missing and row.get(key):
                if row[key] in seen:
                    add(name, i, "duplicate_key",
                        f"'{key}'={row[key]} already used on line {seen[row[key]]}")
                else:
                    seen[row[key]] = i

    for fk in schema.get("foreign_keys", []):
        src, col, dst, dcol = fk["from"], fk["column"], fk["to"], fk["to_column"]
        if src not in tables or dst not in tables:
            continue
        known = {r.get(dcol, "") for r in tables[dst]}
        for i, row in enumerate(tables[src], start=2):
            v = row.get(col, "")
            if v and v not in known:
                add(src, i, "orphan_reference", f"'{col}'={v} not found in {dst}.{dcol}")

    for rule in schema.get("unit_consistency", []):
        # Same SKU must use one unit of measure across a table.
        t = rule["table"]
        if t not in tables:
            continue
        units: dict[str, dict[str, int]] = {}
        for i, row in enumerate(tables[t], start=2):
            k, u = row.get(rule["key"], ""), row.get(rule["unit"], "")
            if k and u:
                units.setdefault(k, {}).setdefault(u, i)
        for k, seen_units in units.items():
            if len(seen_units) > 1:
                line = max(seen_units.values())
                add(t, line, "mixed_units",
                    f"{k} appears with units {sorted(seen_units)}")
    return findings


def render_markdown(findings: list[dict], example: bool = True) -> str:
    out = ["# Go-live readiness report", ""]
    if example:
        out += ["_Data in this report is invented example data._", ""]
    if not findings:
        return "\n".join(out + ["No findings. Export looks ready.", ""])
    by_check: dict[str, int] = {}
    for f in findings:
        by_check[f["check"]] = by_check.get(f["check"], 0) + 1
    out += [f"**{len(findings)} findings**", ""]
    out += [f"- {c}: {n}" for c, n in sorted(by_check.items())]
    out += ["", "| Table | Line | Check | Detail |", "|---|---|---|---|"]
    for f in findings:
        out.append(f"| {f['table']} | {f['row'] or '-'} | {f['check']} | {f['message']} |")
    return "\n".join(out + [""])


def load_schema(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))
