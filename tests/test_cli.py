import os
from random import random
from typing import List

from click.testing import CliRunner
from metabase import PermissionGroup, User

from metabase_manager.cli.main import sync
from tests.helpers import IntegrationTestCase


class CliTests(IntegrationTestCase):
    def setUp(self) -> None:
        super(CliTests, self).setUp()

        self.runner = CliRunner()
        self.fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures/sync/")
        self.config_path = os.path.join(
            os.path.dirname(__file__), "fixtures/sync/metabase.yml"
        )
        self.other_config_path = os.path.join(
            os.path.dirname(__file__), "fixtures/sync/other.yaml"
        )
        self.env = {
            "METABASE_HOST": self.HOST,
            "METABASE_USER": self.EMAIL,
            "METABASE_PASSWORD": self.PASSWORD,
        }

        self.group_to_delete = PermissionGroup.create(
            name=f"{random()}", using=self.metabase
        )

    def tearDown(self) -> None:
        super(CliTests, self).tearDown()

        for user in User.list(using=self.metabase):
            if user.email != self.EMAIL:
                user.delete()

        for group in PermissionGroup.list(using=self.metabase):
            if group.name not in ["All Users", "Administrators"]:
                group.delete()

    def create_or_reactivate_user(
        self, first_name: str, last_name: str, email: str, group_ids: List[int]
    ) -> User:
        try:
            user = User.create(
                using=self.metabase,
                first_name=first_name,
                last_name=last_name,
                email=email,
                group_ids=group_ids,
                password=str(random()),
            )
        except:
            user = User.list(
                using=self.metabase, query=email, include_deactivated=True
            )[0]
            user.reactivate()
        return user

    def test_sync_multiple_files(self):
        """Ensure multiple file options can be passed."""
        result = self.runner.invoke(
            sync, ["-f", self.config_path, "-f", self.other_config_path], env=self.env
        )

        self.assertEqual(0, result.exit_code)

    def test_sync_metabase_credentials(self):
        """Ensure credentials can be provided as environment variables or as CLI options."""
        test_matrix = [
            (
                (sync, ["-f", self.config_path]),  # args
                {},  # kwargs
                2,  # expected exit code
            ),
            (
                (sync, ["-f", self.config_path]),
                {
                    "env": {
                        "METABASE_HOST": self.HOST,
                        "METABASE_USER": self.EMAIL,
                        "METABASE_PASSWORD": self.PASSWORD,
                    }
                },
                0,
            ),
            (
                (
                    sync,
                    [
                        "-f",
                        self.config_path,
                        "--host",
                        self.HOST,
                        "--user",
                        self.EMAIL,
                        "--password",
                        self.PASSWORD,
                    ],
                ),
                {},
                0,
            ),
            (
                (
                    sync,
                    [
                        "-f",
                        self.config_path,
                        "-h",
                        self.HOST,
                        "-u",
                        self.EMAIL,
                        "-p",
                        self.PASSWORD,
                    ],
                ),
                {},
                0,
            ),
        ]

        for args, kwargs, expected in test_matrix:
            result = self.runner.invoke(*args, **kwargs)
            self.assertEqual(expected, result.exit_code)

    def test_sync_silent(self):
        """Ensure metabase-manager sync --silent does not log anything to stdout."""
        result = self.runner.invoke(
            sync, ["-f", self.config_path, "--silent"], env=self.env
        )

        self.assertEqual(0, result.exit_code)
        self.assertEqual("", result.stdout)

    def test_sync_select(self):
        """Ensure --select parameter syncs only specified objects."""
        groups = [g.name for g in PermissionGroup.list(self.metabase)]
        users = [u.email for u in User.list(self.metabase)]
        self.assertTrue("Developers" not in groups)
        self.assertTrue("user2@example.com" not in users)

        result = self.runner.invoke(
            sync, ["-f", self.config_path, "--select", "groups"], env=self.env
        )

        self.assertEqual(0, result.exit_code)
        self.assertTrue(
            "[CREATE] Group(name='Developers')" in result.stdout
        )  # assert logs

        groups = [g.name for g in PermissionGroup.list(self.metabase)]
        self.assertTrue("Developers" in groups)
        self.assertTrue("user2@example.com" not in users)

    def test_sync_exclude(self):
        """Ensure --exclude parameter does not sync specified object."""
        groups = [g.name for g in PermissionGroup.list(self.metabase)]
        users = [u.email for u in User.list(self.metabase)]
        self.assertTrue("Developers" not in groups)
        self.assertTrue("user2@example.com" not in users)

        result = self.runner.invoke(
            sync, ["-f", self.config_path, "--exclude", "users"], env=self.env
        )

        self.assertEqual(0, result.exit_code)
        self.assertTrue(
            "[CREATE] Group(name='Developers')" in result.stdout
        )  # assert logs

        groups = [g.name for g in PermissionGroup.list(self.metabase)]
        self.assertTrue("Developers" in groups)
        self.assertTrue("user2@example.com" not in users)

    def test_sync(self):
        """Ensure sync creates, updates, and deletes objects in Metabase."""
        groups = [g.name for g in PermissionGroup.list(self.metabase)]
        self.assertTrue("Developers" not in groups)
        self.assertTrue(self.group_to_delete.name in groups)

        result = self.runner.invoke(sync, ["-f", self.config_path], env=self.env)

        self.assertEqual(0, result.exit_code)
        self.assertTrue(
            "[CREATE] Group(name='Developers')" in result.stdout
        )  # assert logs

        groups = [g.name for g in PermissionGroup.list(self.metabase)]
        self.assertTrue("Developers" in groups)
        self.assertTrue(self.group_to_delete.name not in groups)

    def test_sync_dry_run(self):
        """Ensure --dry-run results in no commands being executed on Metabase."""
        groups = [g.name for g in PermissionGroup.list(self.metabase)]
        self.assertTrue("Developers" not in groups)

        result = self.runner.invoke(
            sync, ["-f", self.config_path, "--dry-run"], env=self.env
        )

        self.assertEqual(0, result.exit_code)
        self.assertTrue(
            "[CREATE] Group(name='Developers')" in result.stdout
        )  # assert logs
        groups = [g.name for g in PermissionGroup.list(self.metabase)]
        self.assertTrue("Developers" not in groups)

    def test_sync_users(self):
        """Ensure"""
        user1 = self.create_or_reactivate_user(
            first_name="Foo",
            last_name="Bar",
            email="user5@example.com",
            group_ids=[1, 2],
        )
        user2 = self.create_or_reactivate_user(
            first_name="Foo", last_name="Bar", email="user7@example.com", group_ids=[1]
        )
        groups = [g.name for g in PermissionGroup.list(self.metabase)]
        users = [u.email for u in User.list(self.metabase)]

        self.assertTrue("New Group" not in groups)
        self.assertTrue("user4@example.com" not in users)
        self.assertTrue("user5@example.com" in users)
        self.assertTrue("user6@example.com" not in users)
        self.assertTrue("user7@example.com" in users)

        result = self.runner.invoke(
            sync, ["-f", os.path.join(self.fixtures_dir, "users.yaml")], env=self.env
        )
        self.assertEqual(0, result.exit_code)

        groups = PermissionGroup.list(self.metabase)
        users = User.list(self.metabase)

        new_group = next(filter(lambda g: g.name == "New Group", groups))
        self.assertIsNotNone(new_group)  # New Group was created

        # User Four; Create + New Group
        user4 = next(filter(lambda u: u.email == "user4@example.com", users))
        self.assertEqual("User", user4.first_name)
        self.assertEqual("Four", user4.last_name)
        self.assertSetEqual({1, new_group.id}, set(user4.group_ids))

        # User Five; Update
        user5 = next(filter(lambda u: u.email == "user5@example.com", users))
        self.assertEqual("User", user5.first_name)
        self.assertEqual("Five", user5.last_name)
        self.assertSetEqual({1}, set(user5.group_ids))

        # User Six; Unchanged
        user6 = next(filter(lambda u: u.email == "user6@example.com", users))
        self.assertEqual("User", user6.first_name)
        self.assertEqual("Six", user6.last_name)
        self.assertSetEqual({1}, set(user6.group_ids))

    def test_sync_no_delete(self):
        """Ensure --no-delete results in no delete commands being executed on Metabase."""
        group = PermissionGroup.create(using=self.metabase, name="My Group")
        groups = [g.name for g in PermissionGroup.list(self.metabase)]
        self.assertTrue("Developers" not in groups)
        self.assertTrue("My Group" in groups)

        result = self.runner.invoke(
            sync, ["-f", self.config_path, "--no-delete"], env=self.env
        )

        self.assertEqual(0, result.exit_code)

        groups = [g.name for g in PermissionGroup.list(self.metabase)]
        self.assertTrue("Developers" in groups)
        # My Group not in metabase.yaml, it should have been deleted if not --no-delete; assert it still exists
        self.assertTrue("My Group" in groups)

        # assert that without --no-delete, My Group is deleted
        result = self.runner.invoke(sync, ["-f", self.config_path], env=self.env)
        groups = [g.name for g in PermissionGroup.list(self.metabase)]
        self.assertTrue("My Group" not in groups)
