#!/usr/bin/env node
/**
 * Genesis - Ippoc Identity Generator
 * Creates the organism's unique identity and cryptographic keys
 */

import fs from 'fs';
import path from 'path';
import { randomBytes } from 'crypto';

interface Identity {
  nodeId: string;
  publicKey: string;
  privateKey: string;
  createdAt: string;
  version: string;
}

class Genesis {
  private readonly KEY_PATH = './runtime/bootstrap/identity.key';
  private readonly CONFIG_PATH = './system.yaml';

  async generate(): Promise<void> {
    // Check if identity already exists
    if (fs.existsSync(this.KEY_PATH)) {
      console.log('🔑 Identity already exists');
      return;
    }

    console.log('🌱 Generating Ippoc Identity...');

    // Generate unique node ID
    const nodeId = `ippoc-${randomBytes(8).toString('hex')}`;
    
    // Generate keypair (simplified for demo)
    const privateKey = randomBytes(32).toString('hex');
    const publicKey = randomBytes(32).toString('hex');

    const identity: Identity = {
      nodeId,
      publicKey,
      privateKey,
      createdAt: new Date().toISOString(),
      version: '1.0'
    };

    // Save identity
    fs.writeFileSync(this.KEY_PATH, JSON.stringify(identity, null, 2));
    console.log(`✅ Identity generated: ${nodeId}`);
    console.log(`📍 Saved to: ${this.KEY_PATH}`);
  }

  async verify(): Promise<boolean> {
    if (!fs.existsSync(this.KEY_PATH)) {
      console.error('❌ Identity key not found');
      return false;
    }

    try {
      const identity = JSON.parse(fs.readFileSync(this.KEY_PATH, 'utf8'));
      console.log(`✅ Identity verified: ${identity.nodeId}`);
      return true;
    } catch (error) {
      console.error('❌ Invalid identity file');
      return false;
    }
  }
}

// CLI Interface
async function main() {
  const genesis = new Genesis();
  
  const command = process.argv[2] || 'generate';
  
  switch (command) {
    case 'generate':
      await genesis.generate();
      break;
    case 'verify':
      await genesis.verify();
      break;
    default:
      console.log('Usage: genesis [generate|verify]');
  }
}

if (require.main === module) {
  main().catch(console.error);
}

export default Genesis;