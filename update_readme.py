with open("quote_of_the_day.txt") as f:
    quote = f.readline().strip()

with open("README.md") as f:
    readme = f.read()

start = "<!--QUOTE_START-->"
end = "<!--QUOTE_END-->"

new_section = f"{start}\n> {quote}\n{end}"

import re

updated = re.sub(
    f"{start}.*?{end}",
    new_section,
    readme,
    flags=re.DOTALL
)

with open("README.md", "w") as f:
    f.write(updated)
