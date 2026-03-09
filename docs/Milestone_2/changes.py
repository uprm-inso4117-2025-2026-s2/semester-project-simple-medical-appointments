# pymupdf>=1.24,<2

from __future__ import annotations

import argparse
import re
from pathlib import Path

try:
    import pymupdf as fitz
except ImportError:
    try:
        import fitz
    except Exception as exc:
        raise ImportError(
            "PyMuPDF is not installed. Install it with: pip install pymupdf"
        ) from exc

if not hasattr(fitz, "open") or not hasattr(fitz, "Document"):
    raise ImportError(
        "Imported 'fitz' is not PyMuPDF. Uninstall the conflicting package and "
        "reinstall PyMuPDF:\n"
        "  pip uninstall -y fitz frontend\n"
        "  pip install --upgrade pymupdf"
    )


def parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parents[2]
    default_pdf = root / "docs" / "Milestone_2" / "Milestone2.pdf"
    default_changes = root / "full_changes.txt"
    default_output = root / "docs" / "Milestone_2" / "Milestone2_highlighted.pdf"

    parser = argparse.ArgumentParser(
        description=(
            "Apply red/green highlights to Milestone2.pdf from git-style diff data "
            "in full_changes.txt, restricted to docs/Milestone_2/sections."
        )
    )
    parser.add_argument("--pdf", type=Path, default=default_pdf)
    parser.add_argument("--changes", type=Path, default=default_changes)
    parser.add_argument("--output", type=Path, default=default_output)
    parser.add_argument(
        "--section-prefix",
        default="docs/Milestone_2/sections/",
    )
    parser.add_argument(
        "--min-len",
        type=int,
        default=4,
    )
    return parser.parse_args()


def clean_line(line: str) -> str:
    text = line.strip()
    if not text:
        return ""

    text = re.sub(r"^=+\s+", "", text)
    text = re.sub(r"^[\*\-]\s+", "", text)
    text = re.sub(r"^\d+\.\s+", "", text)
    text = text.replace("`", "")
    text = text.replace("*", "")
    text = text.replace("_", "")
    text = re.sub(r"\[\[.*?\]\]", "", text)
    text = re.sub(r"link:[^\[]+\[([^\]]+)\]", r"\1", text)
    text = re.sub(r"image::[^\[]+\[[^\]]*\]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_diff_lines(
    changes_text: str, section_prefix: str, min_len: int
) -> tuple[list[str], list[str]]:
    added: list[str] = []
    removed: list[str] = []
    seen_added: set[str] = set()
    seen_removed: set[str] = set()

    current_file: str | None = None
    in_hunk = False

    for raw in changes_text.splitlines():
        if raw.startswith("diff --git "):
            in_hunk = False
            current_file = None
            parts = raw.split()
            if len(parts) >= 4:
                b_path = parts[3]
                if b_path.startswith("b/"):
                    b_path = b_path[2:]
                if b_path.startswith(section_prefix):
                    current_file = b_path
            continue

        if current_file is None:
            continue

        if raw.startswith("@@"):
            in_hunk = True
            continue

        if not in_hunk:
            continue

        if raw.startswith(("+++", "---", "\\ No newline")):
            continue

        if raw.startswith("+"):
            text = clean_line(raw[1:])
            if len(text) >= min_len and text not in seen_added:
                seen_added.add(text)
                added.append(text)
        elif raw.startswith("-"):
            text = clean_line(raw[1:])
            if len(text) >= min_len and text not in seen_removed:
                seen_removed.add(text)
                removed.append(text)

    return added, removed


def candidate_phrases(text: str) -> list[str]:
    phrases = [text]
    words = text.split()

    if len(words) > 12:
        for i in range(0, len(words), 8):
            chunk = " ".join(words[i : i + 12]).strip()
            if len(chunk) >= 20:
                phrases.append(chunk)

    unique: list[str] = []
    seen: set[str] = set()

    for p in phrases:
        if p not in seen:
            seen.add(p)
            unique.append(p)

    return unique


def add_highlights(
    doc: fitz.Document, lines: list[str], color: tuple[float, float, float]
) -> tuple[int, list[str]]:

    flags = fitz.TEXT_DEHYPHENATE | fitz.TEXT_PRESERVE_LIGATURES
    annotations = 0
    unmatched: list[str] = []

    for line in lines:
        found_for_line = False

        for phrase in candidate_phrases(line):
            phrase_found = False

            for page in doc:
                matches = page.search_for(phrase, quads=True, flags=flags)

                if not matches:
                    continue

                phrase_found = True
                found_for_line = True

                for quad in matches:
                    annot = page.add_highlight_annot(quad)
                    annot.set_colors(stroke=color)
                    annot.update()
                    annotations += 1

            if phrase_found:
                break

        if not found_for_line:
            unmatched.append(line)

    return annotations, unmatched


def print_summary(args, added, removed, add_count, rem_count, add_unmatched, rem_unmatched):
    width = 100
    line = "─" * width

    project_root = Path(__file__).resolve().parents[2]

    def rel(p):
        return p.resolve().relative_to(project_root.parent)

    title = f"PDF HIGHLIGHT REPORT: {args.pdf.name}"

    print("\n" + line)
    print(title.center(width))
    print(line)

    print("\nFiles")
    print(f"  Input PDF      : {rel(args.pdf)}")
    print(f"  Changes file   : {rel(args.changes)}")
    print(f"  Output PDF     : {rel(args.output)}")

    print("\nParsed Changes")
    print(f"  Added lines       : {len(added):>5}")
    print(f"  Removed lines     : {len(removed):>5}")

    print("\nHighlights Created")
    print(f"  Green (added)     : {add_count:>5}")
    print(f"  Red (removed)     : {rem_count:>5}")

    print("\nUnmatched Lines")
    print(f"  Added not found   : {len(add_unmatched):>5}")
    print(f"  Removed not found : {len(rem_unmatched):>5}")

    print("\n" + line + "\n")


def main() -> None:
    args = parse_args()

    if not args.changes.exists():
        raise FileNotFoundError(f"Changes file not found: {args.changes}")

    if not args.pdf.exists():
        raise FileNotFoundError(f"Input PDF not found: {args.pdf}")

    changes_text = args.changes.read_text(encoding="utf-8", errors="replace")

    added, removed = parse_diff_lines(
        changes_text=changes_text,
        section_prefix=args.section_prefix,
        min_len=args.min_len,
    )

    doc = fitz.open(args.pdf)

    try:
        green = (0.0, 0.6, 0.0)
        red = (1.0, 0.0, 0.0)

        add_count, add_unmatched = add_highlights(doc, added, green)
        rem_count, rem_unmatched = add_highlights(doc, removed, red)

        args.output.parent.mkdir(parents=True, exist_ok=True)
        doc.save(args.output)

    finally:
        doc.close()

    print_summary(
        args,
        added,
        removed,
        add_count,
        rem_count,
        add_unmatched,
        rem_unmatched,
    )


if __name__ == "__main__":
    main()