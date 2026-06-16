#!/bin/bash
sed -i 's/baseline: unoptimized forget/memory\/feat: baseline unoptimized forget\n\nDESCRIPTION: revert to baseline\nIMPACT: baseline/' "$1"
