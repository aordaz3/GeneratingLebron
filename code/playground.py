import subprocess

subprocess.run(["git", "status"])

# This script can be scheduled to run every 8 hours using GitHub Actions or a similar scheduling tool. For example, in a GitHub Actions workflow file, you could set it up like this:
# on:
#   schedule:
#     - cron: "0 */8 * * *"