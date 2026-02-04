# Source Integration Guide

IPPOC-OS is now configured to use your **original local source code** for OpenClaw and the Linux kernel.

## 1. OpenClaw Integration
Linked directly from `apps/openclaw-cortex` to `openclaw-main`.

**To apply changes:**
1. Edit code in `openclaw-main`
2. Rebuild cortex:
   ```bash
   cd apps/openclaw-cortex
   pnpm install
   pnpm build
   ```

## 2. Linux Kernel Integration
Linked `drivers/kernel-bridge` to `linux-master`.

**Prerequisites:**
The `linux-master` directory must be prepared for module building:
```bash
cd linux-master
make defconfig
make modules_prepare
```

**To build the module:**
```bash
cd drivers/kernel-bridge
make
```

## Structure
```
ippoc/
├── apps/
│   └── openclaw-cortex/  --> package.json links to ../../../openclaw-main
├── drivers/
│   └── kernel-bridge/    --> Kbuild links to ../../linux-master
├── openclaw-main/        <-- YOUR ORIGINAL SOURCE
└── linux-master/         <-- YOUR ORIGINAL SOURCE
```
