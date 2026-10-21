#!/usr/bin/env python3
"""
Estrae le risposte effettive dal log del benchmark Massaciuccoli Digital Twin
ed esporta un file Excel con una riga per domanda.

Uso:
    python extract_benchmark_outputs.py percorso/al/log.txt
    python extract_benchmark_outputs.py percorso/al/log.txt -o risposte_benchmark.xlsx

Nel foglio Excel:
    - Question: domanda del benchmark
    - Agent Output: solo il contenuto della sezione OUTPUT, senza routing,
      parsing, task execution, timing e altre righe di debug.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter


QUESTION_RE = re.compile(r"^\s*\[.*?\]\s*QUESTION:\s*(.*?)\s*$")
OUTPUT_MARKER = "========== OUTPUT =========="
END_MARKERS = (
    "---------------------------",
    "Ask a question (type 'exit' to quit):",
    "========== NEW REQUEST ==========",
)


def clean_output_block(lines: list[str]) -> str:
    """Rimuove righe vuote iniziali/finali e mantiene solo la risposta."""
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines).strip()


def extract_records(log_text: str) -> list[tuple[str, str]]:
    lines = log_text.splitlines()
    records: list[tuple[str, str]] = []

    current_question: str | None = None
    i = 0

    while i < len(lines):
        match = QUESTION_RE.match(lines[i])
        if match:
            current_question = match.group(1).strip()

        if lines[i].strip() == OUTPUT_MARKER:
            output_lines: list[str] = []
            i += 1

            while i < len(lines):
                line = lines[i]
                stripped = line.strip()

                if stripped in END_MARKERS:
                    break

                # La riga di timing finale non fa parte della risposta.
                if re.match(r"^\[.*?\]\s*\[TIMING\]", stripped):
                    break

                output_lines.append(line)
                i += 1

            answer = clean_output_block(output_lines)
            if current_question:
                records.append((current_question, answer or "[OUTPUT VUOTO]"))
            else:
                records.append(("[DOMANDA NON TROVATA]", answer or "[OUTPUT VUOTO]"))

            continue

        i += 1

    return records


def write_xlsx(records: list[tuple[str, str]], output_path: Path) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "Benchmark outputs"

    ws.append(["Question", "Agent Output"])
    for question, answer in records:
        ws.append([question, answer])

    header_fill = PatternFill("solid", fgColor="D9EAF7")
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.fill = header_fill
        cell.alignment = Alignment(vertical="top", wrap_text=True)

    ws.column_dimensions[get_column_letter(1)].width = 62
    ws.column_dimensions[get_column_letter(2)].width = 100

    for row in ws.iter_rows(min_row=2):
        row[0].alignment = Alignment(vertical="top", wrap_text=True)
        row[1].alignment = Alignment(vertical="top", wrap_text=True)
        # Altezza indicativa per leggere risposte con più righe.
        answer_lines = str(row[1].value or "").count("\n") + 1
        ws.row_dimensions[row[0].row].height = min(max(30, answer_lines * 15), 240)

    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    wb.save(output_path)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Estrae le risposte effettive dal log del benchmark e le salva in Excel."
    )
    parser.add_argument("log_file", help="Percorso del file .txt contenente il log completo")
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="File Excel di destinazione (default: <nome_log>_outputs.xlsx)",
    )
    args = parser.parse_args()

    input_path = Path(args.log_file)
    if not input_path.is_file():
        print(f"Errore: file di log non trovato: {input_path}", file=sys.stderr)
        return 2

    # utf-8-sig gestisce anche file con BOM; errors=replace evita blocchi per
    # eventuali caratteri strani provenienti dal terminale.
    log_text = input_path.read_text(encoding="utf-8-sig", errors="replace")
    records = extract_records(log_text)

    if not records:
        print(
            "Nessuna sezione '========== OUTPUT ==========' trovata. "
            "Controlla che il file contenga il log completo del benchmark.",
            file=sys.stderr,
        )
        return 1

    output_path = (
        Path(args.output)
        if args.output
        else input_path.with_name(f"{input_path.stem}_outputs.xlsx")
    )
    write_xlsx(records, output_path)

    print(f"Domande estratte: {len(records)}")
    print(f"File creato: {output_path.resolve()}")
    print("Colonne: Question, Agent Output")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
