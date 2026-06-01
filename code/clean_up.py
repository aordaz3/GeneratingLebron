from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
RAW_QUOTES_FILE = OUTPUTS_DIR / "lebron_quotes.txt"
CLEANED_QUOTES_FILE = OUTPUTS_DIR / "lebron_quotes_cleaned.txt"


def clean_quotes(lines):
    quotes = []

    for line in lines:
        if "Share this Quote" in line:
            line = line.split("Share this Quote", 1)[0].rstrip() + "\n"

        if "LeBron" not in line and line.strip():
            quotes.append(line)

    return quotes


def main():
    raw = RAW_QUOTES_FILE.read_text(encoding="utf-8").splitlines(keepends=True)
    quotes = clean_quotes(raw)

    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    CLEANED_QUOTES_FILE.write_text("".join(quotes), encoding="utf-8")
    print(f"Wrote {len(quotes)} cleaned quotes to {CLEANED_QUOTES_FILE}")


if __name__ == "__main__":
    main()
