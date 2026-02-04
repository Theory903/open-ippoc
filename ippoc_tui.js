#!/usr/bin/env node

// Minimal IPPOC OpenClaw TUI
const readline = require('readline');
const { spawn } = require('child_process');

class IPPocTUI {
  constructor() {
    this.rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout,
      prompt: 'IPPoc> '
    });
    this.gatewayProcess = null;
    
    this.setupInterface();
  }

  setupInterface() {
    console.log('=== IPPOC OpenClaw Terminal Interface ===');
    console.log('Model: gemini-3-pro-preview');
    console.log('Status: Ready');
    console.log('Commands: start-gateway, stop-gateway, status, quit');
    console.log('');

    this.rl.prompt();

    this.rl.on('line', (line) => {
      const command = line.trim();
      
      switch (command) {
        case 'start-gateway':
          this.startGateway();
          break;
        case 'stop-gateway':
          this.stopGateway();
          break;
        case 'status':
          this.showStatus();
          break;
        case 'quit':
        case 'exit':
          this.quit();
          break;
        case '':
          break;
        default:
          console.log(`Unknown command: ${command}`);
          console.log('Available commands: start-gateway, stop-gateway, status, quit');
      }
      
      this.rl.prompt();
    });

    this.rl.on('close', () => {
      this.quit();
    });
  }

  startGateway() {
    if (this.gatewayProcess) {
      console.log('Gateway is already running');
      return;
    }

    console.log('Starting IPPOC Gateway...');
    
    this.gatewayProcess = spawn('node', ['dist/entry.js', 'gateway'], {
      cwd: './mind/openclaw',
      stdio: 'pipe',
      env: {
        ...process.env,
        GATEWAY_MODEL: 'gemini-3-pro-preview',
        MODEL_PROVIDER: 'google',
        OPENCLAW_GATEWAY_TOKEN: 'ippoc-secret-key',
        OPENCLAW_SKIP_CHANNELS: '1',
        CLAWDBOT_SKIP_CHANNELS: '1'
      }
    });

    this.gatewayProcess.stdout.on('data', (data) => {
      console.log(`[Gateway] ${data.toString().trim()}`);
    });

    this.gatewayProcess.stderr.on('data', (data) => {
      console.error(`[Gateway Error] ${data.toString().trim()}`);
    });

    this.gatewayProcess.on('close', (code) => {
      console.log(`Gateway process exited with code ${code}`);
      this.gatewayProcess = null;
    });

    console.log('Gateway started successfully');
  }

  stopGateway() {
    if (!this.gatewayProcess) {
      console.log('Gateway is not running');
      return;
    }

    console.log('Stopping gateway...');
    this.gatewayProcess.kill();
    this.gatewayProcess = null;
    console.log('Gateway stopped');
  }

  showStatus() {
    console.log('=== IPPOC Status ===');
    console.log(`Gateway: ${this.gatewayProcess ? 'Running' : 'Stopped'}`);
    console.log('Model: gemini-3-pro-preview');
    console.log('Provider: Google');
    console.log('Configuration: Loaded');
  }

  quit() {
    console.log('Shutting down IPPOC TUI...');
    if (this.gatewayProcess) {
      this.gatewayProcess.kill();
    }
    this.rl.close();
    process.exit(0);
  }
}

// Start the TUI
new IPPocTUI();