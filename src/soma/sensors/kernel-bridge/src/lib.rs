// SPDX-License-Identifier: GPL-2.0

//! IPPOC-OS Kernel Bridge
//! 
//! Main entry point for the kernel module

#![no_std]
#![cfg_attr(feature = "kernel-module", feature(allocator_api))]

#[cfg(feature = "kernel-module")]
mod ippoc_sensor;

#[cfg(feature = "kernel-module")]
pub use ippoc_sensor::*;
