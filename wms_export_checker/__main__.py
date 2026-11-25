import argparse
import sys
from pathlib import Path

from .core import check_export, load_schema, render_markdown


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="wms-export-checker", description=__doc__)
    p.add_argument("folder", type=Path, help="folder with one CSV per table")
    p.add_argument("--schema", type=Path, required=True, help="schema JSON")
    p.add_argument("--out", type=Path, help="write the markdown report here")
    p.add_argument("--real-data", action="store_true",
                   help="omit the 'invented example data' note")
    a = p.parse_args(argv)
    findings = check_export(a.folder, load_schema(a.schema))
    report = render_markdown(findings, example=not a.real_data)
    if a.out:
        a.out.write_text(report, encoding="utf-8")
    print(report)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
