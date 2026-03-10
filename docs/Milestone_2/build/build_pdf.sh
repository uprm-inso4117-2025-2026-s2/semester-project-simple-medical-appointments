#!/usr/bin/env bash
set -euo pipefail

input="documentation.adoc"
output="Milestone-2.pdf"

while [[ $# -gt 0 ]]; do
  case "$1" in
    -i|--input) input="$2"; shift 2 ;;
    -o|--output) output="$2"; shift 2 ;;
    *) echo "Usage: $0 [-i input.adoc] [-o output.pdf]"; exit 1 ;;
  esac
done

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd "$here/.." && pwd)"
ext="$here/section_role_propagator.rb"
themes="$here"

cd "$root"
asciidoctor-pdf --failure-level ERROR -a "pdf-themesdir=$themes" -a "pdf-theme=highlighting-theme.yml" -r "$ext" "$input" -o "$output"
echo "Built PDF: $output"
