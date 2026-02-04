# IPPOC OpenClaw Fork Management

This directory contains the IPPOC fork of OpenClaw with synchronization scripts to keep it updated from the upstream repository.

## Setup

The upstream remote is already configured:
```bash
git remote add upstream https://github.com/openclaw/openclaw.git
```

## Update Scripts

### Check for Updates
```bash
# Using pnpm script
pnpm update:check

# Or directly
./scripts/check-updates.sh
```

### Apply Updates
```bash
# Using pnpm script
pnpm update:apply

# Or directly
./scripts/update-from-upstream.sh
```

## How It Works

1. **Check Updates**: Compares local HEAD with upstream/main and shows available commits
2. **Apply Updates**: 
   - Creates a backup branch before merging
   - Attempts to merge upstream changes
   - Runs build test to verify compatibility
   - Reverts changes if build fails

## Safety Features

- Automatic backup branch creation before updates
- Build verification after merging
- Automatic rollback on build failures
- Conflict detection with manual resolution guidance

## Branch Strategy

- `ippoc-main`: Your IPPOC fork with customizations (pushes to `origin/ippoc-main`)
- `master`: Local development branch 
- `upstream/main`: Tracking the official OpenClaw repository
- Backup branches: Created automatically during updates (named `backup-before-update-YYYYMMDD-HHMMSS`)

## Manual Update Process

If you prefer manual control:

```bash
# Fetch upstream changes
git fetch upstream

# Check what's available
git log --oneline HEAD..upstream/main

# Create backup branch
git branch backup-$(date +%Y%m%d-%H%M%S)

# Merge upstream changes
git merge upstream/main

# Test build
pnpm build

# If build fails, revert:
# git reset --hard HEAD~1
```

## IPPOC Customizations

This fork includes IPPOC-specific modifications:
- `gemini-3-pro-preview` model support
- Custom TUI interface (`ippoc_tui.js`)
- IPPOC branding and configuration
- Modified model normalization in `models-config.providers.ts`

These customizations are preserved during updates, but may require manual conflict resolution if upstream changes affect the same files.