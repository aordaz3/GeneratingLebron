import collections
import random
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
TRAINING_FILE = OUTPUTS_DIR / "lebron_interview_quotes.txt"
DAILY_QUOTE_FILE = OUTPUTS_DIR / "daily_quote.txt"


def build_markov_model(file_path):
    words = Path(file_path).read_text(encoding="utf-8").lower().split()
    if len(words) < 2:
        raise ValueError(f"Not enough training text in {file_path}")
    
    # Map each word to a list of words that follow it
    model = collections.defaultdict(list)
    for i in range(len(words) - 1):
        model[words[i]].append(words[i+1])
    return model

def predict_next_word(model, current_word):
    current_word = current_word.lower()
    if current_word in model:
        # Randomly choose from words that have followed this word before
        return random.choice(model[current_word])
    return None


def generate_quote(model, seed="i", min_words=6, max_words=18):
    seed = seed.lower()
    if seed not in model:
        seed = random.choice(list(model))

    words = [seed]
    current_word = seed

    while len(words) < max_words:
        next_word = predict_next_word(model, current_word)
        if next_word is None:
            break

        words.append(next_word)
        current_word = next_word

        if len(words) >= min_words and next_word.endswith((".", "!", "?")):
            break

    quote = " ".join(words)
    return quote[:1].upper() + quote[1:]


def main():
    markov_model = build_markov_model(TRAINING_FILE)
    quote = generate_quote(markov_model)

    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    DAILY_QUOTE_FILE.write_text(quote + "\n", encoding="utf-8")
    print(quote)


if __name__ == "__main__":
    main()
