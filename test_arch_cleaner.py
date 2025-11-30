import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add current directory to path to import arch_cleaner
sys.path.append(os.getcwd())
from arch_cleaner import ArchCleaner

class TestArchCleaner(unittest.TestCase):
    def setUp(self):
        self.cleaner = ArchCleaner(dry_run=True)

    @patch('subprocess.run')
    def test_check_orphans_found(self, mock_run):
        # Mock pacman -Qtdq returning orphans
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="pkg1\npkg2\n"
        )
        orphans = self.cleaner.check_orphans()
        self.assertEqual(orphans, ["pkg1", "pkg2"])

    @patch('subprocess.run')
    def test_check_orphans_none(self, mock_run):
        # Mock pacman -Qtdq returning error (no orphans)
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout=""
        )
        orphans = self.cleaner.check_orphans()
        self.assertEqual(orphans, [])

    @patch('builtins.print')
    def test_run_command_dry_run(self, mock_print):
        self.cleaner.dry_run = True
        self.cleaner.run_command(["ls", "-l"])
        mock_print.assert_called_with("[DRY-RUN] Would execute: ls -l")

    @patch('subprocess.run')
    @patch('os.geteuid')
    def test_clean_cache_paccache(self, mock_geteuid, mock_run):
        self.cleaner.dry_run = False # Disable dry_run to trigger subprocess.run
        # Mock running as root to avoid sudo
        mock_geteuid.return_value = 0
        
        # Mock 'which paccache' returning success
        mock_run.side_effect = [
            MagicMock(returncode=0), # which paccache
            MagicMock(returncode=0)  # paccache -r
        ]
        self.cleaner.clean_cache()
        
        args_list = [call.args[0] for call in mock_run.call_args_list]
        self.assertIn(["paccache", "-r"], args_list)

    @patch('os.listdir')
    @patch('os.path.exists')
    @patch('builtins.print')
    def test_remove_partial_downloads(self, mock_print, mock_exists, mock_listdir):
        mock_exists.return_value = True
        mock_listdir.return_value = ["package.pkg.tar.zst.part", "other.file"]
        
        self.cleaner.remove_partial_downloads()
        
        # Should print that it would remove the .part file
        # Since we are in dry_run=True (from setUp), it prints [DRY-RUN]
        mock_print.assert_any_call("[DRY-RUN] Would remove: /var/cache/pacman/pkg/package.pkg.tar.zst.part")

    @patch('subprocess.run')
    @patch('os.geteuid')
    @patch('builtins.print')
    def test_check_config_files(self, mock_print, mock_geteuid, mock_run):
        mock_geteuid.return_value = 0 # Root
        
        mock_run.return_value = MagicMock(
            stdout="/etc/pacman.d/mirrorlist.pacnew\n/etc/passwd.pacsave\n"
        )
        
        self.cleaner.check_config_files()
        
        mock_print.assert_any_call("  /etc/pacman.d/mirrorlist.pacnew")
        mock_print.assert_any_call("  /etc/passwd.pacsave")

if __name__ == '__main__':
    unittest.main()
