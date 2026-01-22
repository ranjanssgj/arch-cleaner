# Arch Cleaner

A lightweight CLI utility to keep your Arch Linux system clean and organized.

## Features

- **Orphan Removal**: Identifies and removes unused dependencies (`pacman -Qtdq`).
- **Cache Cleaning**: Cleans package cache using `paccache` (keeps 3 versions) or falls back to `pacman -Sc`.
- **Partial Downloads**: Removes `.part` files from `/var/cache/pacman/pkg/`.
- **Config Files**: Lists `.pacnew` and `.pacsave` files in `/etc/` for manual review.
- **Dry Run**: `--dry-run` flag to simulate actions without making changes (default safety mechanism).

## Installation

### Using PKGBUILD (Recommended)

1.  Clone this repository:
    ```bash
    git clone https://github.com/ranjanssgj/arch-cleaner.git
    cd arch-cleaner
    ```
2.  Build and install:
    ```bash
    makepkg -si
    ```

### Manual Installation

Copy `arch_cleaner.py` to your path:
```bash
sudo install -Dm755 arch_cleaner.py /usr/bin/arch-cleaner
```

## Usage

Run `arch-cleaner` from the terminal. Sudo privileges are required for actual cleanup operations.

```bash
# Run all checks in dry-run mode (safe, prints what would happen)
arch-cleaner --all --dry-run

# Run specific checks
arch-cleaner --remove-orphans --dry-run
arch-cleaner --clean-cache --dry-run
arch-cleaner --check-configs

# Execute cleanup (requires sudo/root)
sudo arch-cleaner --all
```

## License

GPL-3.0
