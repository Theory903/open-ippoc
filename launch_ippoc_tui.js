#!/usr/bin/env node

// IPPOC OpenClaw TUI Launcher
import { spawn } from 'child_process';
import { join } from 'path';

const openclawPath = join(process.cwd(), 'mind', 'openclaw');

// Set environment variables for IPPOC configuration
process.env.OPENCLAW_PROFILE = 'ippoc';
process.env.CLAWDBOT_PROFILE = 'ippoc';
process.env.GATEWAY_MODEL = 'gemini-3-pro-preview';
process.env.MODEL_PROVIDER = 'google';

console.log('=== IPPOC OpenClaw TUI ===');
console.log('Launching with IPPOC configuration...');
console.log('Model: gemini-3-pro-preview');
console.log('Provider: google');
console.log('');

// Spawn the TUI process
const tui = spawn('pnpm', ['tui:dev'], {
  cwd: openclawPath,
  stdio: 'inherit',
  env: {
    ...process.env,
    OPENCLAW_PROFILE: 'ippoc',
    CLAWDBOT_PROFILE: 'ippoc',
    GATEWAY_MODEL: 'gemini-3-pro-preview',
    MODEL_PROVIDER: 'google'
  }
});

tui.on('close', (code) => {
  console.log(`\nTUI exited with code ${code}`);
});

tui.on('error', (error) => {
  console.error('Failed to start TUI:', error.message);
});