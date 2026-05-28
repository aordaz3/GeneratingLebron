import random
import collections

def build_markov_model(file_path):
    with open(file_path, 'r') as f:
        words = f.read().lower().split()
    
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
    return "Word not found in training data."

# Usage
file_name = '/Users/aordaz3/CurProjects/LearningGit/lebron_quotes_cleaned.txt' 
markov_model = build_markov_model(file_name)
seed = "I"

ran = random.randint(0, 16)
quote = seed
for i in range(ran):
    next_word = predict_next_word(markov_model, seed)
    seed = next_word
    quote += " " + next_word

print(quote)
