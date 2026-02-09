#!/usr/bin/env python3
"""
Checksum Verification Script for Soma Binaries

This script generates and verifies SHA-256 checksums for Soma binaries
to ensure supply chain integrity.
"""

import hashlib
import os
import sys
import argparse
from pathlib import Path


def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 checksum of a file."""
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()


def find_binary_files(root_dir: Path, binary_extensions: list = None) -> list:
    """Find binary files in the given directory."""
    if binary_extensions is None:
        binary_extensions = [".exe", ".bin", ".so", ".dll", ".dylib", ".a", ".lib"]
    
    binary_files = []
    for file_path in root_dir.rglob("*"):
        if file_path.is_file():
            if any(file_path.suffix == ext for ext in binary_extensions) or \
               (file_path.name.startswith("soma") and not file_path.suffix):
                binary_files.append(file_path)
    return binary_files


def generate_checksums(output_file: str, root_dir: str = None) -> None:
    """Generate checksums for all binary files."""
    if root_dir is None:
        root_dir = Path(__file__).parent.parent / "src" / "soma"
    
    binary_files = find_binary_files(Path(root_dir))
    
    with open(output_file, "w") as f:
        for file_path in binary_files:
            rel_path = file_path.relative_to(root_dir)
            checksum = calculate_sha256(file_path)
            f.write(f"{checksum}  {rel_path}\n")
    
    print(f"Generated checksums for {len(binary_files)} files in {output_file}")


def verify_checksums(checksum_file: str, root_dir: str = None) -> bool:
    """Verify checksums against stored values."""
    if root_dir is None:
        root_dir = Path(__file__).parent.parent / "src" / "soma"
    
    all_valid = True
    
    with open(checksum_file, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
                
            checksum, rel_path = line.split("  ", 1)
            file_path = Path(root_dir) / rel_path
            
            if not file_path.exists():
                print(f"ERROR: File not found: {rel_path}")
                all_valid = False
                continue
                
            calculated = calculate_sha256(file_path)
            if calculated != checksum:
                print(f"ERROR: Checksum mismatch for {rel_path}")
                print(f"  Expected: {checksum}")
                print(f"  Calculated: {calculated}")
                all_valid = False
            else:
                print(f"OK: {rel_path}")
    
    return all_valid


def main():
    parser = argparse.ArgumentParser(
        description="Soma Binary Checksum Verification Tool"
    )
    
    subparsers = parser.add_subparsers(title="Commands", dest="command")
    
    # Generate checksums command
    gen_parser = subparsers.add_parser("generate", help="Generate checksum file")
    gen_parser.add_argument(
        "-o", "--output",
        default="checksums.sha256",
        help="Output file name (default: checksums.sha256)"
    )
    gen_parser.add_argument(
        "-r", "--root",
        help="Root directory to scan for binaries (default: src/soma)"
    )
    
    # Verify checksums command
    verify_parser = subparsers.add_parser("verify", help="Verify checksums")
    verify_parser.add_argument(
        "checksum_file",
        help="Checksum file to verify"
    )
    verify_parser.add_argument(
        "-r", "--root",
        help="Root directory for binary files (default: src/soma)"
    )
    
    args = parser.parse_args()
    
    if args.command == "generate":
        generate_checksums(args.output, args.root)
    elif args.command == "verify":
        if verify_checksums(args.checksum_file, args.root):
            print("\nAll checksums valid")
            sys.exit(0)
        else:
            print("\nChecksum verification failed")
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
