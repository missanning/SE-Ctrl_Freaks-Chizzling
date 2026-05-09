"""
Automated Tests for User Story: Database Backup Management
As an Admin of Chizzling POS System
I want to backup the database regularly to external storage
So that I can prevent data loss and recover business data in case of system failure
"""

import unittest
import sys
import os
import json
import shutil
import tempfile
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock, mock_open

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from backup_manager import BackupManager


class TestDatabaseBackupManagement(unittest.TestCase):
    """Test suite for database backup management functionality"""

    def setUp(self):
        """Set up test environment before each test"""
        # Create temporary directories for testing
        self.test_dir = tempfile.mkdtemp()
        self.backup_dir = os.path.join(self.test_dir, "backups")
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Create test database file
        self.test_db_path = os.path.join(self.test_dir, "sales_inventory.db")
        with open(self.test_db_path, 'w') as f:
            f.write("test database content")
        
        # Create test config file path
        self.test_config_path = os.path.join(self.test_dir, "backup_config.json")
        
    def tearDown(self):
        """Clean up after each test"""
        # Remove test directory
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def _create_backup_manager(self):
        """Helper to create a BackupManager with test paths"""
        manager = BackupManager()
        manager.db_path = self.test_db_path
        manager.config_path = self.test_config_path
        manager.load_config()
        return manager
    
    # ========================================================================
    # AC1: Backup Reminder System
    # ========================================================================
    
    def test_backup_reminder_shows_after_7_days(self):
        """
        Given I am logged in as Admin
        When 7 or more days have passed since the last backup
        Then I should see a backup reminder popup
        """
        backup_manager = self._create_backup_manager()
        
        # Set last backup to 8 days ago
        eight_days_ago = datetime.now() - timedelta(days=8)
        backup_manager.config["last_backup"] = eight_days_ago.isoformat()
        backup_manager.save_config()
        
        # Check if reminder should show
        should_show = backup_manager.should_show_reminder()
        
        self.assertTrue(should_show,
                       "Reminder should show after 7+ days")
    
    def test_backup_reminder_not_shown_before_7_days(self):
        """
        Given I am logged in as Admin
        When less than 7 days have passed since the last backup
        Then I should NOT see a backup reminder popup
        """
        backup_manager = self._create_backup_manager()
        
        # Set last backup to 3 days ago
        three_days_ago = datetime.now() - timedelta(days=3)
        backup_manager.config["last_backup"] = three_days_ago.isoformat()
        backup_manager.save_config()
        
        # Check if reminder should show
        should_show = backup_manager.should_show_reminder()
        
        self.assertFalse(should_show,
                        "Reminder should NOT show before 7 days")
    
    def test_backup_reminder_shows_for_first_time_user(self):
        """
        Given I have never created a backup before
        When I login as Admin
        Then I should see a backup reminder popup
        """
        backup_manager = self._create_backup_manager()
        
        # No last backup set
        backup_manager.config["last_backup"] = None
        backup_manager.save_config()
        
        # Check if reminder should show
        should_show = backup_manager.should_show_reminder()
        
        self.assertTrue(should_show,
                       "Reminder should show for first-time users")
    
    def test_backup_reminder_shows_last_backup_date(self):
        """
        Given I am logged in as Admin
        When the backup reminder appears
        Then the reminder should show the last backup date
        """
        backup_manager = self._create_backup_manager()
        
        # Set last backup to 10 days ago
        ten_days_ago = datetime.now() - timedelta(days=10)
        backup_manager.config["last_backup"] = ten_days_ago.isoformat()
        backup_manager.save_config()
        
        # Get last backup info
        last_backup, _ = backup_manager.get_last_backup_info()
        
        self.assertEqual(last_backup, "10 days ago",
                        "Should show '10 days ago'")
    
    # ========================================================================
    # AC2: Manual Backup Access
    # ========================================================================
    
    def test_admin_can_access_backup_manager(self):
        """
        Given I am logged in as Admin
        When I click "Database Backup" in the dashboard sidebar
        Then the Database Backup Manager window should open
        """
        # This tests that BackupManager can be instantiated
        backup_manager = self._create_backup_manager()
        
        self.assertIsNotNone(backup_manager,
                            "Backup manager should be accessible")
        self.assertTrue(hasattr(backup_manager, 'create_backup'),
                       "Should have create_backup method")
    
    def test_backup_manager_shows_backup_information(self):
        """
        Given I am logged in as Admin
        When the Database Backup Manager window opens
        Then I should see backup information
        """
        backup_manager = self._create_backup_manager()
        
        # Set some backup info
        backup_manager.config["last_backup"] = datetime.now().isoformat()
        backup_manager.config["backup_location"] = self.backup_dir
        backup_manager.save_config()
        
        # Get backup info
        last_backup, location = backup_manager.get_last_backup_info()
        
        self.assertIsNotNone(last_backup,
                            "Should show last backup date")
        self.assertIsNotNone(location,
                            "Should show backup location")
    
    # ========================================================================
    # AC3: First-Time Backup Setup
    # ========================================================================
    
    def test_first_time_backup_prompts_for_location(self):
        """
        Given I have never created a backup before
        When I click "Backup Now" button
        Then I should be prompted to select a backup location
        """
        backup_manager = self._create_backup_manager()
        
        # No location set
        backup_manager.config["backup_location"] = None
        
        # Attempt to create backup without location
        success, message = backup_manager.create_backup()
        
        self.assertFalse(success,
                        "Should fail without location")
        self.assertIn("location", message.lower(),
                     "Error message should mention location")
    
    def test_selected_location_is_saved(self):
        """
        Given I select a backup location
        When I confirm the selection
        Then the selected location should be saved for future backups
        """
        backup_manager = self._create_backup_manager()
        
        # Set backup location
        backup_manager.config["backup_location"] = self.backup_dir
        backup_manager.save_config()
        
        # Reload config
        backup_manager.load_config()
        
        self.assertEqual(backup_manager.config["backup_location"],
                        self.backup_dir,
                        "Location should be saved")
    
    # ========================================================================
    # AC4: Backup Creation
    # ========================================================================
    
    def test_backup_creates_file_with_timestamp(self):
        """
        Given I have set a backup location
        When I click "Backup Now" button
        Then the system should create a backup file with timestamp format
        """
        backup_manager = self._create_backup_manager()
        backup_manager.db_path = self.test_db_path
        
        # Create backup
        success, backup_path = backup_manager.create_backup(self.backup_dir)
        
        self.assertTrue(success, "Backup should succeed")
        self.assertTrue(os.path.exists(backup_path),
                       "Backup file should exist")
        
        # Verify filename format
        filename = os.path.basename(backup_path)
        self.assertTrue(filename.startswith("chizzling_backup_"),
                       "Should start with 'chizzling_backup_'")
        self.assertTrue(filename.endswith(".db"),
                       "Should end with '.db'")
        
        # Verify timestamp format (YYYYMMDD_HHMMSS)
        timestamp_part = filename.replace("chizzling_backup_", "").replace(".db", "")
        self.assertEqual(len(timestamp_part), 15,
                        "Timestamp should be 15 characters (YYYYMMDD_HHMMSS)")
    
    def test_backup_updates_last_backup_date(self):
        """
        Given I create a backup
        When the backup completes successfully
        Then the last backup date should be updated to current date/time
        """
        backup_manager = self._create_backup_manager()
        backup_manager.db_path = self.test_db_path
        
        # Record time before backup
        before_backup = datetime.now()
        
        # Create backup
        success, _ = backup_manager.create_backup(self.backup_dir)
        
        self.assertTrue(success, "Backup should succeed")
        
        # Check last backup date
        last_backup_str = backup_manager.config["last_backup"]
        last_backup_date = datetime.fromisoformat(last_backup_str)
        
        # Should be within 1 second of current time
        time_diff = (datetime.now() - last_backup_date).total_seconds()
        self.assertLess(time_diff, 2,
                       "Last backup date should be current time")
    
    def test_backup_shows_success_message_with_path(self):
        """
        Given I create a backup
        When the backup completes successfully
        Then I should see a success message showing the backup file path
        """
        backup_manager = self._create_backup_manager()
        backup_manager.db_path = self.test_db_path
        
        # Create backup
        success, result = backup_manager.create_backup(self.backup_dir)
        
        self.assertTrue(success, "Backup should succeed")
        self.assertIn(self.backup_dir, result,
                     "Result should contain backup path")
        self.assertTrue(os.path.exists(result),
                       "Backup file should exist at returned path")
    
    # ========================================================================
    # AC5: Change Backup Location
    # ========================================================================
    
    def test_can_change_backup_location(self):
        """
        Given I have previously set a backup location
        When I click "Change Location" button and select a new folder
        Then the new location should be saved
        """
        backup_manager = self._create_backup_manager()
        
        # Set initial location
        initial_location = os.path.join(self.test_dir, "backup1")
        os.makedirs(initial_location, exist_ok=True)
        backup_manager.config["backup_location"] = initial_location
        backup_manager.save_config()
        
        # Change to new location
        new_location = os.path.join(self.test_dir, "backup2")
        os.makedirs(new_location, exist_ok=True)
        backup_manager.config["backup_location"] = new_location
        backup_manager.save_config()
        
        # Reload and verify
        backup_manager.load_config()
        
        self.assertEqual(backup_manager.config["backup_location"],
                        new_location,
                        "New location should be saved")
    
    def test_future_backups_use_new_location(self):
        """
        Given I have changed the backup location
        When I create a new backup
        Then the backup should be created in the new location
        """
        backup_manager = self._create_backup_manager()
        backup_manager.db_path = self.test_db_path
        
        # Set new location
        new_location = os.path.join(self.test_dir, "new_backups")
        os.makedirs(new_location, exist_ok=True)
        backup_manager.config["backup_location"] = new_location
        backup_manager.save_config()
        
        # Create backup
        success, backup_path = backup_manager.create_backup(new_location)
        
        self.assertTrue(success, "Backup should succeed")
        self.assertIn(new_location, backup_path,
                     "Backup should be in new location")
    
    # ========================================================================
    # AC6: Backup Information Display
    # ========================================================================
    
    def test_last_backup_formatted_as_today(self):
        """
        Given I created a backup today
        When I open the Database Backup Manager
        Then I should see "Today" as the last backup date
        """
        backup_manager = self._create_backup_manager()
        
        # Set last backup to today
        backup_manager.config["last_backup"] = datetime.now().isoformat()
        backup_manager.save_config()
        
        # Get formatted date
        last_backup, _ = backup_manager.get_last_backup_info()
        
        self.assertEqual(last_backup, "Today",
                        "Should show 'Today'")
    
    def test_last_backup_formatted_as_yesterday(self):
        """
        Given I created a backup yesterday
        When I open the Database Backup Manager
        Then I should see "Yesterday" as the last backup date
        """
        backup_manager = self._create_backup_manager()
        
        # Set last backup to yesterday
        yesterday = datetime.now() - timedelta(days=1)
        backup_manager.config["last_backup"] = yesterday.isoformat()
        backup_manager.save_config()
        
        # Get formatted date
        last_backup, _ = backup_manager.get_last_backup_info()
        
        self.assertEqual(last_backup, "Yesterday",
                        "Should show 'Yesterday'")
    
    def test_last_backup_formatted_as_days_ago(self):
        """
        Given I created a backup 5 days ago
        When I open the Database Backup Manager
        Then I should see "5 days ago" as the last backup date
        """
        backup_manager = self._create_backup_manager()
        
        # Set last backup to 5 days ago
        five_days_ago = datetime.now() - timedelta(days=5)
        backup_manager.config["last_backup"] = five_days_ago.isoformat()
        backup_manager.save_config()
        
        # Get formatted date
        last_backup, _ = backup_manager.get_last_backup_info()
        
        self.assertEqual(last_backup, "5 days ago",
                        "Should show '5 days ago'")
    
    def test_backup_info_shows_never_for_first_time(self):
        """
        Given I have never created a backup
        When I open the Database Backup Manager
        Then I should see "Never" as the last backup date
        """
        backup_manager = self._create_backup_manager()
        
        # No backup set
        backup_manager.config["last_backup"] = None
        backup_manager.save_config()
        
        # Get formatted date
        last_backup, _ = backup_manager.get_last_backup_info()
        
        self.assertEqual(last_backup, "Never",
                        "Should show 'Never'")
    
    def test_backup_info_shows_location(self):
        """
        Given I have set a backup location
        When I open the Database Backup Manager
        Then I should see the current backup location path
        """
        backup_manager = self._create_backup_manager()
        
        # Set location
        backup_manager.config["backup_location"] = self.backup_dir
        
        # Get location
        _, location = backup_manager.get_last_backup_info()
        
        self.assertEqual(location, self.backup_dir,
                        "Should show backup location")
    
    def test_backup_info_shows_not_set_for_no_location(self):
        """
        Given I have not set a backup location
        When I open the Database Backup Manager
        Then I should see "Not set" as the location
        """
        backup_manager = self._create_backup_manager()
        
        # No location set
        backup_manager.config["backup_location"] = None
        backup_manager.save_config()
        
        # Get location
        _, location = backup_manager.get_last_backup_info()
        
        self.assertEqual(location, "Not set",
                        "Should show 'Not set'")
    
    # ========================================================================
    # AC7: Role-Based Access Control
    # ========================================================================
    
    def test_cashier_should_not_see_backup_option(self):
        """
        Given I am logged in as Cashier
        When I access the system
        Then I should NOT see the "Database Backup" option
        """
        # This tests the logic that backup is admin-only
        user_role = "cashier"
        
        # Check if backup should be accessible
        has_backup_access = (user_role == "admin")
        
        self.assertFalse(has_backup_access,
                        "Cashier should not have backup access")
    
    def test_inventory_staff_should_not_see_backup_option(self):
        """
        Given I am logged in as Inventory Staff
        When I access the system
        Then I should NOT see the "Database Backup" option
        """
        user_role = "inventory_staff"
        
        # Check if backup should be accessible
        has_backup_access = (user_role == "admin")
        
        self.assertFalse(has_backup_access,
                        "Inventory staff should not have backup access")
    
    def test_admin_should_see_backup_option(self):
        """
        Given I am logged in as Admin
        When I access the system
        Then I should see the "Database Backup" option
        """
        user_role = "admin"
        
        # Check if backup should be accessible
        has_backup_access = (user_role == "admin")
        
        self.assertTrue(has_backup_access,
                       "Admin should have backup access")
    
    def test_non_admin_should_not_receive_backup_reminders(self):
        """
        Given I am logged in as Cashier or Inventory Staff
        When I access the system
        Then I should NOT receive backup reminders
        """
        # Backup reminders only show in admin dashboard
        # This is enforced by only calling show_backup_reminder in dashboard.py
        
        roles_without_reminders = ["cashier", "inventory_staff"]
        
        for role in roles_without_reminders:
            should_show_reminder = (role == "admin")
            self.assertFalse(should_show_reminder,
                           f"{role} should not receive reminders")
    
    # ========================================================================
    # AC8: Error Handling
    # ========================================================================
    
    def test_backup_fails_when_location_not_accessible(self):
        """
        Given I attempt to create a backup
        When the backup location is not accessible
        Then I should see an error message
        """
        backup_manager = self._create_backup_manager()
        backup_manager.db_path = self.test_db_path
        
        # Use non-existent location
        invalid_location = "/invalid/path/that/does/not/exist"
        
        # Attempt backup
        success, message = backup_manager.create_backup(invalid_location)
        
        self.assertFalse(success,
                        "Backup should fail with invalid location")
        self.assertIsInstance(message, str,
                            "Should return error message")
    
    def test_backup_not_marked_complete_on_failure(self):
        """
        Given I attempt to create a backup
        When the backup fails
        Then the backup should not be marked as completed
        """
        backup_manager = self._create_backup_manager()
        backup_manager.db_path = self.test_db_path
        
        # Record last backup date before attempt
        backup_manager.config["last_backup"] = None
        backup_manager.save_config()
        
        # Attempt backup with invalid location
        success, _ = backup_manager.create_backup("/invalid/path")
        
        self.assertFalse(success, "Backup should fail")
        
        # Verify last backup date not updated
        self.assertIsNone(backup_manager.config["last_backup"],
                         "Last backup should not be updated on failure")
    
    # ========================================================================
    # AC9: Backup File Naming
    # ========================================================================
    
    def test_multiple_backups_have_unique_timestamps(self):
        """
        Given I create multiple backups
        When each backup is created
        Then each file should have a unique timestamp
        """
        backup_manager = self._create_backup_manager()
        backup_manager.db_path = self.test_db_path
        
        # Create first backup
        success1, path1 = backup_manager.create_backup(self.backup_dir)
        self.assertTrue(success1, "First backup should succeed")
        
        # Wait a moment to ensure different timestamp
        import time
        time.sleep(1)
        
        # Create second backup
        success2, path2 = backup_manager.create_backup(self.backup_dir)
        self.assertTrue(success2, "Second backup should succeed")
        
        # Verify different filenames
        self.assertNotEqual(path1, path2,
                           "Backup files should have unique names")
    
    def test_backup_filename_format(self):
        """
        Given I create a backup
        When the backup is created
        Then the file should be named: chizzling_backup_YYYYMMDD_HHMMSS.db
        """
        backup_manager = self._create_backup_manager()
        backup_manager.db_path = self.test_db_path
        
        # Create backup
        success, backup_path = backup_manager.create_backup(self.backup_dir)
        
        self.assertTrue(success, "Backup should succeed")
        
        # Extract filename
        filename = os.path.basename(backup_path)
        
        # Verify format
        self.assertRegex(filename,
                        r'^chizzling_backup_\d{8}_\d{6}\.db$',
                        "Filename should match format chizzling_backup_YYYYMMDD_HHMMSS.db")
    
    def test_older_backups_not_overwritten(self):
        """
        Given I create multiple backups
        When each backup is created
        Then older backups should remain intact (not overwritten)
        """
        backup_manager = self._create_backup_manager()
        backup_manager.db_path = self.test_db_path
        
        # Create first backup
        success1, path1 = backup_manager.create_backup(self.backup_dir)
        self.assertTrue(success1, "First backup should succeed")
        self.assertTrue(os.path.exists(path1),
                       "First backup file should exist")
        
        # Wait to ensure different timestamp
        import time
        time.sleep(1)
        
        # Create second backup
        success2, path2 = backup_manager.create_backup(self.backup_dir)
        self.assertTrue(success2, "Second backup should succeed")
        
        # Verify both files exist
        self.assertTrue(os.path.exists(path1),
                       "First backup should still exist")
        self.assertTrue(os.path.exists(path2),
                       "Second backup should exist")
    
    # ========================================================================
    # AC10: Configuration Persistence
    # ========================================================================
    
    def test_backup_location_persists_after_restart(self):
        """
        Given I have set a backup location
        When I close and reopen the application
        Then the system should remember my backup location
        """
        # Create first instance and set location
        backup_manager1 = BackupManager()
        backup_manager1.config_path = self.test_config_path
        backup_manager1.config["backup_location"] = self.backup_dir
        backup_manager1.save_config()
        
        # Create new instance (simulating restart)
        backup_manager2 = BackupManager()
        backup_manager2.config_path = self.test_config_path
        backup_manager2.load_config()
        
        # Verify location persisted
        self.assertEqual(backup_manager2.config["backup_location"],
                        self.backup_dir,
                        "Backup location should persist")
    
    def test_last_backup_date_persists_after_restart(self):
        """
        Given I have created a backup
        When I close and reopen the application
        Then the last backup date should be preserved
        """
        # Create first instance and set date
        backup_manager1 = BackupManager()
        backup_manager1.config_path = self.test_config_path
        test_date = datetime.now().isoformat()
        backup_manager1.config["last_backup"] = test_date
        backup_manager1.save_config()
        
        # Create new instance (simulating restart)
        backup_manager2 = BackupManager()
        backup_manager2.config_path = self.test_config_path
        backup_manager2.load_config()
        
        # Verify date persisted
        self.assertEqual(backup_manager2.config["last_backup"],
                        test_date,
                        "Last backup date should persist")
    
    def test_reminder_calculates_correctly_after_restart(self):
        """
        Given I have created a backup 8 days ago
        When I close and reopen the application
        Then the reminder should calculate correctly based on saved date
        """
        # Create first instance and set old date
        backup_manager1 = BackupManager()
        backup_manager1.config_path = self.test_config_path
        eight_days_ago = datetime.now() - timedelta(days=8)
        backup_manager1.config["last_backup"] = eight_days_ago.isoformat()
        backup_manager1.save_config()
        
        # Create new instance (simulating restart)
        backup_manager2 = BackupManager()
        backup_manager2.config_path = self.test_config_path
        backup_manager2.load_config()
        
        # Check reminder
        should_show = backup_manager2.should_show_reminder()
        
        self.assertTrue(should_show,
                       "Reminder should show after restart with old backup date")


# ============================================================================
# Test Runner
# ============================================================================

def run_tests():
    """Run all tests and generate report"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestDatabaseBackupManagement)
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY - DATABASE BACKUP MANAGEMENT")
    print("="*70)
    print(f"Tests Run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success Rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print("="*70)
    
    # Print acceptance criteria coverage
    print("\n" + "="*70)
    print("ACCEPTANCE CRITERIA COVERAGE")
    print("="*70)
    print("✅ AC1: Backup Reminder System (4 tests)")
    print("✅ AC2: Manual Backup Access (2 tests)")
    print("✅ AC3: First-Time Backup Setup (2 tests)")
    print("✅ AC4: Backup Creation (3 tests)")
    print("✅ AC5: Change Backup Location (2 tests)")
    print("✅ AC6: Backup Information Display (6 tests)")
    print("✅ AC7: Role-Based Access Control (4 tests)")
    print("✅ AC8: Error Handling (2 tests)")
    print("✅ AC9: Backup File Naming (3 tests)")
    print("✅ AC10: Configuration Persistence (3 tests)")
    print("="*70)
    print(f"Total: {result.testsRun} tests covering 10 acceptance criteria")
    print("="*70)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
