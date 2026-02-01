// SPDX-License-Identifier: GPL-2.0

//! IPPOC-OS Kernel Bridge
//! 
//! Main entry point for the kernel module

#![no_std]
#![feature(allocator_api)]

mod ippoc_sensor;

pub use ippoc_sensor::*;
