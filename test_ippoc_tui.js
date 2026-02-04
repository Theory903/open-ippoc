#!/usr/bin/env node

// Test script for IPPOC OpenClaw TUI
const { spawn } = require('child_process');

console.log('=== IPPOC OpenClaw TUI Test ===');
console.log('Testing gateway functionality with gemini-3-pro-preview model');
console.log('');

// Test the gateway directly first
console.log('1. Testing gateway directly:');
const gatewayTest = spawn('node', ['./mind/openclaw/dist/entry.js', 'gateway'], {
  env: {
    ...process.env,
    GATEWAY_MODEL: 'gemini-3-pro-preview',
    MODEL_PROVIDER: 'google'
  }
});

gatewayTest.stdout.on('data', (data) => {
  console.log(`[Direct Gateway] ${data.toString().trim()}`);
});

gatewayTest.on('close', (code) => {
  console.log(`Direct gateway test completed with code ${code}`);
  
  // Now test the TUI
  console.log('\n2. Testing IPPOC TUI:');
  console.log('Run: node ippoc_tui.js');
  console.log('Then use commands: start-gateway, status, quit');
});

setTimeout(() => {
  gatewayTest.kill();
}, 3000);