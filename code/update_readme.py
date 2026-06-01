from pathlib import Path
import re


PROJECT_ROOT = Path(__file__).resolve().parents[1]
QUOTE_FILE = PROJECT_ROOT / "outputs" / "daily_quote.txt"
README_FILE = PROJECT_ROOT / "README.md"

start = "<!--QUOTE_START-->"
end = "<!--QUOTE_END-->"


def main():
    quote = QUOTE_FILE.read_text(encoding="utf-8").strip() or "Quote will appear here"
    readme = README_FILE.read_text(encoding="utf-8")

    new_section = f"{start}\n> {quote}\n{end}"

    updated = re.sub(
        f"{re.escape(start)}.*?{re.escape(end)}",
        new_section,
        readme,
        flags=re.DOTALL,
    )

    README_FILE.write_text(updated, encoding="utf-8")


if __name__ == "__main__":
    main()
