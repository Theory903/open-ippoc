#!/bin/bash
# IPPOC Platform Level 1 Structure Discovery

echo "--- IPPOC PLATFORM STRUCTURE (Depth 3) ---"
# Using find to get a tree-like view up to level 3, excluding common hidden folders
find . -maxdepth 3 -not -path '*/.*' -not -path '*/__pycache__*' -not -path './target*' -not -path './node_modules*' | sed -e "s/[^-][^\/]*\// |/g" -e "s/|\([^ ]\)/|-- \1/"
