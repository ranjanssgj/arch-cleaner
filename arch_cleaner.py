#!/usr/bin/env python3
import argparse
import subprocess
import sys
import os
from typing import List

class ArchCleaner:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run

    def run_command(self, command: List[str], require_sudo: bool = False) -> bool:
        """
        Executes a command.
        If dry_run is True, prints the command instead.
        """
        if require_sudo and os.geteuid() != 0:
            command = ["sudo"] + command

        cmd_str = " ".join(command)
        if self.dry_run:
            print(f"[DRY-RUN] Would execute: {cmd_str}")
            return True
        
        print(f"Executing: {cmd_str}")
        try:
            subprocess.run(command, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error executing command: {e}", file=sys.stderr)
            return False

    def check_orphans(self):
        """
        Checks for orphaned packages using 'pacman -Qtdq'.
        Returns a list of orphan packages.
        """
        print("Checking for orphaned packages...")
        try:
            # pacman -Qtdq returns a list of orphans, one per line.
            # If no orphans, it returns non-zero exit code (usually 1).
            result = subprocess.run(
                ["pacman", "-Qtdq"], 
                capture_output=True, 
                text=True, 
                check=False
            )
            
            if result.returncode != 0:
                print("No orphans found.")
                return []
            
            orphans = result.stdout.strip().split('\n')
            orphans = [o for o in orphans if o] # Filter empty strings
            return orphans
        except FileNotFoundError:
            print("Error: 'pacman' not found. Is this an Arch Linux system?", file=sys.stderr)
            return []

    def remove_orphans(self):
        orphans = self.check_orphans()
        if not orphans:
            return

        print(f"Found {len(orphans)} orphan packages: {', '.join(orphans)}")
        
        if not self.dry_run:
            confirm = input("Do you want to remove them? [y/N] ").strip().lower()
            if confirm != 'y':
                print("Skipping orphan removal.")
                return

        # pacman -Rns <orphans>
        cmd = ["pacman", "-Rns"] + orphans
        self.run_command(cmd, require_sudo=True)

    def clean_cache(self):
        """
        Cleans package cache.
        Tries to use 'paccache -r' (keep 3 versions) first.
        """
        print("Cleaning package cache...")
        # Check if paccache exists
        if subprocess.run(["which", "paccache"], capture_output=True).returncode == 0:
            self.run_command(["paccache", "-r"], require_sudo=True)
        else:
            print("Warning: 'paccache' not found (part of pacman-contrib).")
            print("Falling back to 'pacman -Sc' (removes uninstalled packages from cache).")
            if not self.dry_run:
                confirm = input("Run 'pacman -Sc'? [y/N] ").strip().lower()
                if confirm == 'y':
                    self.run_command(["pacman", "-Sc"], require_sudo=True)
            else:
                self.run_command(["pacman", "-Sc"], require_sudo=True)

    def remove_partial_downloads(self):
        """
        Removes .part files from /var/cache/pacman/pkg/
        """
        cache_dir = "/var/cache/pacman/pkg/"
        print(f"Checking for partial downloads in {cache_dir}...")
        
        if not os.path.exists(cache_dir):
            print(f"Cache directory {cache_dir} does not exist.")
            return

        partial_files = []
        try:
            for f in os.listdir(cache_dir):
                if f.endswith(".part"):
                    partial_files.append(os.path.join(cache_dir, f))
        except PermissionError:
            print(f"Permission denied accessing {cache_dir}. Try running with sudo.")
            return

        if not partial_files:
            print("No partial downloads found.")
            return

        print(f"Found {len(partial_files)} partial files.")
        for f in partial_files:
            if self.dry_run:
                print(f"[DRY-RUN] Would remove: {f}")
            else:
                print(f"Removing: {f}")
                try:
                    # Need sudo to remove files in /var/cache/pacman/pkg/ usually
                    # But os.remove might fail if not root.
                    # Let's use run_command with rm to handle sudo if needed
                    self.run_command(["rm", f], require_sudo=True)
                except Exception as e:
                    print(f"Error removing {f}: {e}")

    def check_config_files(self):
        """
        Checks for .pacnew and .pacsave files in /etc/
        """
        print("Checking for .pacnew and .pacsave files in /etc/...")
        # find /etc -name "*.pacnew" -o -name "*.pacsave"
        cmd = ["find", "/etc", "-name", "*.pacnew", "-o", "-name", "*.pacsave"]
        
        try:
            # find returns 0 even if nothing found, but prints to stdout
            # We might get permission denied errors on stderr, so we should handle that or use sudo
            # But searching /etc usually requires sudo for full coverage? 
            # Actually many files in /etc are readable. But some dirs are not.
            # Let's try without sudo first, and suppress stderr? Or just run with sudo if available?
            # The plan said "Locate ... List them".
            # Let's use sudo if not root to be sure we see everything.
            
            if os.geteuid() != 0:
                cmd = ["sudo"] + cmd
                
            result = subprocess.run(cmd, capture_output=True, text=True)
            files = result.stdout.strip().split('\n')
            files = [f for f in files if f]
            
            if not files:
                print("No .pacnew or .pacsave files found.")
                return

            print(f"Found {len(files)} configuration files to review:")
            for f in files:
                print(f"  {f}")
            print("Tip: Use 'pacdiff' or manually merge these files.")
            
        except Exception as e:
            print(f"Error searching for config files: {e}")

def main():
    parser = argparse.ArgumentParser(description="Arch Linux System Cleaner Utility")
    parser.add_argument("--dry-run", action="store_true", help="Simulate commands without executing them")
    parser.add_argument("--remove-orphans", action="store_true", help="Check and remove orphaned packages")
    parser.add_argument("--clean-cache", action="store_true", help="Clean package cache (keep 3 versions)")
    parser.add_argument("--remove-partial", action="store_true", help="Remove partial download (.part) files")
    parser.add_argument("--check-configs", action="store_true", help="Check for .pacnew and .pacsave files")
    parser.add_argument("--all", action="store_true", help="Run all cleanup tasks")
    
    args = parser.parse_args()

    cleaner = ArchCleaner(dry_run=args.dry_run)

    if args.all or args.remove_orphans:
        cleaner.remove_orphans()
    
    if args.all or args.clean_cache:
        cleaner.clean_cache()
        
    if args.all or args.remove_partial:
        cleaner.remove_partial_downloads()

    if args.all or args.check_configs:
        cleaner.check_config_files()
    
    if not any([args.remove_orphans, args.clean_cache, args.remove_partial, args.check_configs, args.all]):
        parser.print_help()

if __name__ == "__main__":
    main()
