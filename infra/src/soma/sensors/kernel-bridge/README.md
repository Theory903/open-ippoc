# IPPOC Kernel Module

## Overview

The IPPOC kernel module (`ippoc_sensor`) provides a `/dev/ippoc` character device for userspace communication with the kernel.

## Features

- **Read**: Get system metrics (CPU, memory, uptime)
- **Write**: Send bounded actuation commands
- **Safety**: All commands are validated and sandboxed

## Building

### Prerequisites

- Linux kernel with Rust support enabled
- Rust toolchain matching kernel version

### Build Steps

```bash
cd drivers/kernel-bridge

# Build module
make

# Load module (requires root)
sudo insmod ippoc_sensor.ko

# Verify
ls -l /dev/ippoc
```

## Usage

### Read Metrics

```bash
# Read system metrics
cat /dev/ippoc
# Output: {"cpu_usage":15.2,"memory_mb":2048,"uptime_seconds":3600}
```

### Send Commands

```bash
# Send bounded command
echo "nice_process:1234" > /dev/ippoc
```

### From Rust (ippoc-node)

```rust
use std::fs::{File, OpenOptions};
use std::io::{Read, Write};

// Read metrics
let mut file = File::open("/dev/ippoc")?;
let mut metrics = String::new();
file.read_to_string(&mut metrics)?;
println!("Metrics: {}", metrics);

// Send command
let mut file = OpenOptions::new().write(true).open("/dev/ippoc")?;
file.write_all(b"nice_process:1234")?;
```

## Architecture

```
┌─────────────────────────────────┐
│  Userspace (ippoc-node)         │
│  - Read metrics                 │
│  - Send commands                │
└──────────────┬──────────────────┘
               │ /dev/ippoc
┌──────────────▼──────────────────┐
│  Kernel Module (ippoc_sensor)   │
│  - file::Operations             │
│  - Bounded command validation   │
└──────────────┬──────────────────┘
               │
┌──────────────▼──────────────────┐
│  Linux Kernel                   │
│  - Process management           │
│  - System metrics               │
└─────────────────────────────────┘
```

## Bounded Commands

Only safe, validated commands are allowed:

- `nice_process:PID` - Adjust process priority
- `limit_memory:PID:MB` - Set memory limit
- `throttle_cpu:PID:PERCENT` - CPU throttling

All commands are logged and rate-limited.

## Unloading

```bash
sudo rmmod ippoc_sensor
```
