import os
from random import randint

from click.testing import CliRunner
from metabase import PermissionGroup, User

from metabase_manager.cli.main import sync
from tests.helpers import IntegrationTestCase


class CliTests(IntegrationTestCase):
    def setUp(self) -> None:
        super(CliTests, self).setUp()

        self.user_to_delete = User.create(
            first_name="user",
            last_name="one",
            email=f"{randint(0, 1000)}@example.com",
            password="123",
            using=self.metabase,
        )

        self.group_to_delete = PermissionGroup.create(
            name=f"{randint(0, 1000)}", using=self.metabase
        )

    def tearDown(self) -> None:
        super(CliTests, self).tearDown()

        for user in User.list(using=self.metabase):
            if user.email != self.EMAIL:
                user.delete()

        for group in PermissionGroup.list(using=self.metabase):
            if group.name not in ["All Users", "Administrators"]:
                group.delete()

    def test_sync(self):
        """Ensure metabase-manager sync --dry-run does not call .create(), .update(), .delete() methods."""
        runner = CliRunner()
        filepath = os.path.join(os.path.dirname(__file__), "fixtures/sync/metabase.yml")

        result = runner.invoke(
            sync,
            [
                "-f",
                filepath,
                "--host",
                self.HOST,
                "--user",
                self.EMAIL,
                "--password",
                self.PASSWORD,
            ],
        )

        self.assertEqual(0, result.exit_code)
        self.assertTrue("[CREATE] Group(name='Read-Only')" in result.stdout)
        self.assertTrue(
            f"[DELETE] Group(name='{self.group_to_delete.name}')" in result.stdout
        )
        self.assertTrue(
            "[CREATE] User(first_name='User', last_name='One', email='user1@example.com', groups=['Administrators', 'Developers'])"
            in result.stdout
        )
        self.assertTrue(
            "[CREATE] User(first_name='User', last_name='Two', email='user2@example.com', groups=['Developers'])"
            in result.stdout
        )
        self.assertTrue(
            f"[DELETE] User(first_name='user', last_name='one', email='{self.user_to_delete.email}', groups='<Unknown>')"
            in result.stdout,
            result.stdout,
        )

        groups = [g.name for g in PermissionGroup.list(using=self.metabase)]
        emails = [u.email for u in User.list(using=self.metabase)]
        self.assertTrue("Read-Only" in groups)
        self.assertTrue(self.group_to_delete.name not in groups)
        self.assertTrue("user1@example.com" in emails)
        self.assertTrue("user2@example.com" in emails)
        self.assertTrue(self.user_to_delete.email not in emails)

    def test_sync_dry_run(self):
        """Ensure metabase-manager sync --dry-run does not call .create(), .update(), .delete() methods."""
        runner = CliRunner()
        filepath = os.path.join(os.path.dirname(__file__), "fixtures/sync/metabase.yml")

        result = runner.invoke(
            sync,
            [
                "-f",
                filepath,
                "--host",
                self.HOST,
                "--user",
                self.EMAIL,
                "--password",
                self.PASSWORD,
                "--dry-run",
            ],
        )

        self.assertEqual(0, result.exit_code)
        self.assertTrue("[CREATE] Group(name='Read-Only')" in result.stdout)
        self.assertTrue(
            f"[DELETE] Group(name='{self.group_to_delete.name}')" in result.stdout
        )
        self.assertTrue(
            "[CREATE] User(first_name='User', last_name='One', email='user1@example.com', groups=['Administrators', 'Developers'])"
            in result.stdout
        )
        self.assertTrue(
            "[CREATE] User(first_name='User', last_name='Two', email='user2@example.com', groups=['Developers'])"
            in result.stdout
        )
        self.assertTrue(
            f"[DELETE] User(first_name='user', last_name='one', email='{self.user_to_delete.email}', groups='<Unknown>')"
            in result.stdout,
            result.stdout,
        )

        groups = [g.name for g in PermissionGroup.list(using=self.metabase)]
        emails = [u.email for u in User.list(using=self.metabase)]
        self.assertTrue("Read-Only" not in groups)
        self.assertTrue(self.group_to_delete.name in groups)
        self.assertTrue("user1@example.com" not in emails)
        self.assertTrue("user2@example.com" not in emails)
        self.assertTrue(self.user_to_delete.email in emails)
