#!/usr/bin/env node
import process from "node:process";

console.log('[DEBUG] Entry point received args:');
console.log('process.argv:', process.argv);
console.log('process.argv.slice(2):', process.argv.slice(2));

// Simulate what run-main.ts does
const stripWindowsNodeExec = (argv) => {
  return argv;
};

const normalizedArgv = stripWindowsNodeExec(process.argv);
console.log('normalizedArgv:', normalizedArgv);

// Import and test the CLI logic
const { getCommandPath, getPrimaryCommand } = await import('./dist/cli/argv.js');

console.log('getCommandPath(normalizedArgv, 2):', getCommandPath(normalizedArgv, 2));
console.log('getPrimaryCommand(normalizedArgv):', getPrimaryCommand(normalizedArgv));