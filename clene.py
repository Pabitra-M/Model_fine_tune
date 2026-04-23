"""
Clean training data: remove URLs from answers so they don't
contradict the system prompt rule "never output URLs".

Usage:
    python clean_data.py --input output_qa.json --output output_qa_clean.json
"""

import json
import re
import argparse
from pathlib import Path


# ── Patterns to remove ────────────────────────────────────────────────────────
URL_PATTERNS = [
    # <https://...> or <http://...>  (angle-bracket wrapped)
    r'<https?://[^\s>]+>',
    # plain https:// or http://
    r'https?://[^\s\)\]\,\"\']+',
    # www.something.com
    r'\bwww\.[^\s\)\]\,\"\']+',
]

# Numbered list steps that say "visit X website / go to X" — optionally remove
STEP_PATTERNS = [
    # lines like:  1. Visit the official U.S. Navy website at ...
    r'\n?\s*\d+\.\s+Visit the official[^\n]+',
    # lines like:  2. Use the search function ...
    # (keep these — they are fine, just remove the URL inside them)
]

COMBINED_URL_RE = re.compile('|'.join(URL_PATTERNS), re.IGNORECASE)


def clean_answer(text: str) -> str:
    # Remove URLs
    text = COMBINED_URL_RE.sub('', text)

    # Fix broken phrases like "at ." or "at,"  left after URL removal
    text = re.sub(r'\bat\s+([,\.\)])', r'\1', text)
    text = re.sub(r'\bat\s*$', '', text, flags=re.MULTILINE)

    # Collapse multiple blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Strip trailing whitespace per line
    text = '\n'.join(line.rstrip() for line in text.splitlines())

    return text.strip()


def process_file(input_path: str, output_path: str):
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not isinstance(data, list):
        data = [data]

    cleaned = 0
    results = []

    for i, item in enumerate(data):
        answer_key = 'answer' if 'answer' in item else 'output'
        original   = item.get(answer_key, '')
        cleaned_ans = clean_answer(original)

        if cleaned_ans != original:
            cleaned += 1
            print(f"[{i+1}] Cleaned URLs from: {item.get('question', item.get('instruction', ''))[:70]}...")

        item[answer_key] = cleaned_ans
        results.append(item)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nDone. {cleaned}/{len(results)} records had URLs removed.")
    print(f"Saved → {output_path}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input',  default='output_qa.json',       help='Input JSON file')
    parser.add_argument('--output', default='output_qa_clean.json', help='Output JSON file')
    args = parser.parse_args()

    process_file(args.input, args.output)