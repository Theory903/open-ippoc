#!/bin/bash
GIT_SEQUENCE_EDITOR="sed -i 's/^pick \(.*\) baseline: unoptimized forget/reword \1 baseline: unoptimized forget/'" GIT_EDITOR="./fix_msg_editor.sh" git rebase -i HEAD~2
