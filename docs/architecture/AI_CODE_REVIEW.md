# AI Code Review Integration

## Overview

IPPOC-OS uses **CodeRabbit AI PR Reviewer** for automated code review. It provides:
- Line-by-line code suggestions
- PR summaries and release notes
- Security and performance analysis
- IPPOC-OS specific architectural checks

---

## GitHub Actions (Automatic)

The AI reviewer runs automatically on every pull request.

### Setup

1. **Add OpenAI API Key** to GitHub Secrets:
   - Go to repository Settings → Secrets → Actions
   - Add `OPENAI_API_KEY` with your OpenAI API key

2. **Create PR** - The review will run automatically

3. **Interact with Bot**:
   ```
   @coderabbitai Please generate a test plan for this file
   @coderabbitai Explain the biological analogy here
   @coderabbitai Is this safe for self-evolution?
   ```

### Configuration

See [.github/workflows/ai-pr-reviewer.yml](file:///Users/abhishekjha/Downloads/ippoc/.github/workflows/ai-pr-reviewer.yml)

**Custom System Message:**
- Understands IPPOC-OS architecture
- Checks for safety in self-evolution
- Validates distributed system patterns
- Ensures kernel operations are bounded

---

## Local Review (Manual)

Use the standalone script for local code review before committing.

### Usage

```bash
# Review a single file
./tools/review_code.sh libs/hidb/src/lib.rs

# Review entire directory
./tools/review_code.sh apps/openclaw-cortex/

# Review all changes
./tools/review_code.sh
```

### What It Checks

1. **Static Analysis**
   - Rust: `cargo clippy`
   - TypeScript: `eslint`

2. **Tests**
   - Runs package-specific tests
   - Shows test coverage

3. **AI Review**
   - Architectural patterns
   - Safety considerations
   - Performance implications
   - Security vulnerabilities

---

## Review Focus Areas

### Safety
- ✅ Bounded resource usage
- ✅ No unbounded syscalls
- ✅ WorldModel simulation coverage
- ✅ Proper error handling

### Performance
- ✅ Sub-millisecond P2P latency
- ✅ Async I/O in hot paths
- ✅ Memory allocation patterns
- ✅ Cache efficiency

### Architecture
- ✅ Biological analogies documented
- ✅ Distributed system correctness
- ✅ HiDB semantic operations
- ✅ Git evolution safety

---

## Example Review Output

```
=== AI Review Summary ===

File: libs/git-evolution/src/lib.rs

Key Observations:
- Proper use of libgit2 for version control
- Async simulation integration
- Error handling with Result<T>

Suggestions:
1. Add rollback test for failed simulations
2. Document merge conflict resolution strategy
3. Consider rate limiting for auto-merge

Security:
✓ No direct filesystem access
✓ Simulation required before merge
✓ Bounded branch creation

Performance:
- Git operations are blocking - consider async wrapper
- Branch cleanup could be batched

Action Items:
[ ] Add test for concurrent patch proposals
[ ] Document WorldModel integration
[ ] Profile merge performance

Overall: LGTM with minor suggestions
```

---

## Ignoring Reviews

To skip AI review for a PR, add to description:

```
@coderabbitai: ignore
```

---

## Cost Estimation

- **gpt-3.5-turbo** (summaries): ~$0.01 per PR
- **gpt-4** (detailed review): ~$0.50-$2.00 per PR
- **Typical monthly cost** (20 developers): ~$20-40

---

## Advanced Usage

### Custom Prompts

Edit `.github/workflows/ai-pr-reviewer.yml` to customize:

```yaml
system_message: |
  Focus on:
  - Memory safety in Rust
  - Async patterns in TypeScript
  - Kernel module safety
```

### Review Specific Files

```yaml
path_filters:
  - 'libs/**/*.rs'
  - 'apps/**/*.ts'
  - '!**/*.test.ts'
```

---

## Troubleshooting

**Review not running?**
- Check GitHub Actions permissions
- Verify `OPENAI_API_KEY` is set
- Ensure PR is from same repository (not fork)

**Review too verbose?**
- Set `review_simple_changes: false`
- Set `review_comment_lgtm: false`

**Want faster reviews?**
- Use `gpt-3.5-turbo` for both models
- Enable `review_simple_changes: false`

---

## Integration with IPPOC-OS

The AI reviewer is **IPPOC-OS aware**:
- Understands biological/cellular model
- Validates self-evolution safety
- Checks distributed system patterns
- Ensures kernel operations are bounded

This makes it an integral part of the **GitEvolution** self-modification pipeline:
1. Code change proposed
2. AI review (this tool)
3. WorldModel simulation
4. Auto-merge if safe

---

**Learn more:** [CodeRabbit Documentation](https://github.com/coderabbitai/ai-pr-reviewer)
