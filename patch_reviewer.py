import sys

filepath = ".github/workflows/ai-pr-reviewer.yml"
with open(filepath, "r") as f:
    content = f.read()

content = content.replace("coderabbitai/ai-pr-reviewer@latest", "coderabbitai/openai-pr-reviewer@latest")

with open(filepath, "w") as f:
    f.write(content)
