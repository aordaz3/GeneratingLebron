

with open("/Users/aordaz3/CurProjects/LearningGit/lebron_quotes.txt", "r") as file:
    raw = file.readlines()

quotes = []

for line in raw:
    # 1. Clean the tail phrase if it exists
    if "Share this Quote" in line:
        line = line.split("Share this Quote", 1)[0].rstrip() + "\n"
    
    # 2. Filter out lines containing "LeBron" (using the cleaned line)
    if "LeBron" not in line:
        quotes.append(line)

with open("/Users/aordaz3/CurProjects/LearningGit/lebron_quotes_cleaned.txt", "w") as file:
    file.writelines(quotes)


