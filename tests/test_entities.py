from dataclasses import dataclass
from unittest import TestCase
from unittest.mock import patch

import metabase
from metabase import PermissionGroup
from requests import HTTPError

from metabase_manager.entities import Entity, Group, User


class EntityTests(TestCase):
    def test_load(self):
        @dataclass
        class MockEntity(Entity):
            id: int
            name: str

        entity = MockEntity.load({"id": 2, "name": "my_name"})
        self.assertEqual(entity.id, 2)
        self.assertEqual(entity.name, "my_name")

    def test_key_raises_error(self):
        with self.assertRaises(NotImplementedError):
            entity = Entity()
            _ = entity.key

    def test_get_key_from_metabase_instance_raises_error(self):
        with self.assertRaises(NotImplementedError):
            entity = Entity()
            _ = entity.get_key_from_metabase_instance(resource=None)

    def test_from_resource(self):
        with self.assertRaises(NotImplementedError):
            entity = Entity()
            _ = entity.from_resource(resource=None)

    def test_can_delete(self):
        entity = Entity()
        self.assertTrue(entity.can_delete(resource=None))

    def test_is_equal_raises_error(self):
        with self.assertRaises(NotImplementedError):
            entity = Entity()
            _ = entity.is_equal(resource=None)

    def test_create_raises_error(self):
        with self.assertRaises(NotImplementedError):
            entity = Entity()
            _ = entity.create(using=None)

    def test_update_raises_error(self):
        with self.assertRaises(NotImplementedError):
            entity = Entity()
            _ = entity.update()

    def test_delete_raises_error(self):
        with self.assertRaises(NotImplementedError):
            entity = Entity()
            _ = entity.delete()


class GroupTests(TestCase):
    def test_key(self):
        """Ensure Group.key returns its name."""
        group = Group(name="my_name")
        self.assertEqual("my_name", group.key)

    def test_is_equal(self):
        """Ensure Group.is_equal() returns True if a PermissionGroup has the same name."""
        group = Group(name="my_name")

        self.assertTrue(group.is_equal(PermissionGroup(name="my_name", _using=None)))
        self.assertFalse(group.is_equal(PermissionGroup(name="abc", _using=None)))

    def test_can_delete(self):
        """
        Ensure Group.can_delete() returns True if the PermissionGroup.name
        is not in Group._PROTECTED.
        """
        group = Group(name="my_name")

        self.assertTrue(group.can_delete(PermissionGroup(name="valid", _using=None)))
        self.assertFalse(group.can_delete(PermissionGroup(name="All Users", _using=None)))
        self.assertFalse(group.can_delete(PermissionGroup(name="Administrators", _using=None)))

    def test_get_key_from_metabase_instance(self):
        """Ensure Group.get_key_from_metabase_instance() returns the PermissionGroup name."""
        self.assertEqual(
            "my_name",
            Group.get_key_from_metabase_instance(
                PermissionGroup(name="my_name", _using=None)
            ),
        )

    def test_from_resource(self):
        """Ensure Group.from_resource() returns an instance of Group from a PermissionGroup."""
        permission_group = PermissionGroup(name="my_name", _using=None)
        group = Group.from_resource(permission_group)

        self.assertIsInstance(group, Group)
        self.assertEqual("my_name", group.name)
        self.assertEqual(group.resource, permission_group)

    def test_create(self):
        """Ensure Group.create() calls PermissionGroup.create()."""
        with patch.object(metabase.PermissionGroup, "create") as c:
            group = Group(name="my_group")
            group.create(using=None)

            self.assertIsNone(c.assert_called_with(using=None, name="my_group"))

    def test_update(self):
        """
        Ensure Group.update() does nothing. PermissionGroup should not be
        updated since the only attribute is the  key.
        """
        with patch.object(metabase.PermissionGroup, "update") as c:
            group = Group(name="my_group")
            group.update()

            self.assertIsNone(c.assert_not_called())

    def test_delete(self):
        """Ensure Group.delete() calls delete() on the provided class."""
        with patch.object(metabase.PermissionGroup, "delete") as c:
            metabase_group = metabase.PermissionGroup(name="my_group", _using=None)
            group = Group(name="my_group", resource=metabase_group)
            group.delete()
            self.assertTrue(c.called)

    def test_delete_protected(self):
        """
        Ensure Group.delete() does not call delete() on the provided
        class if the name is in self._PROTECTED_GROUPS.
        """
        with patch.object(metabase.PermissionGroup, "delete") as c:
            group = Group(name="my_group", resource=metabase.PermissionGroup(name="All Users", _using=None))
            group.delete()

            self.assertFalse(c.called)


class UserTests(TestCase):
    def test_key(self):
        """Ensure User.key returns its name."""
        user = User(
            email="my_email", first_name="my_first_name", last_name="my_last_name"
        )
        self.assertEqual("my_email", user.key)

    def test_is_equal(self):
        """Ensure User.is_equal() returns True if a metabase.User has the same name."""
        user = User(
            email="my_email", first_name="my_first_name", last_name="my_last_name"
        )

        self.assertTrue(
            user.is_equal(
                metabase.User(
                    email="my_email",
                    first_name="my_first_name",
                    last_name="my_last_name",
                    _using=None,
                )
            )
        )
        self.assertFalse(
            user.is_equal(
                metabase.User(
                    email="not_my_email",
                    first_name="my_first_name",
                    last_name="my_last_name",
                    _using=None,
                )
            )
        )

    def test_get_key_from_metabase_instance(self):
        """Ensure User.get_key_from_metabase_instance() returns the PermissionGroup name."""
        self.assertEqual(
            "my_email",
            User.get_key_from_metabase_instance(
                metabase.User(email="my_email", _using=None)
            ),
        )

    def test_from_resource(self):
        """Ensure User.from_resource() returns an instance of User from a metabase.User."""
        metabase_user = metabase.User(
            first_name="my_name",
            last_name="my_last_name",
            email="test@example.com",
            _using=None
        )
        user = User.from_resource(metabase_user)

        self.assertIsInstance(user, User)
        self.assertEqual("my_name", user.first_name)
        self.assertEqual("my_last_name", user.last_name)
        self.assertEqual("test@example.com", user.email)

        # when from_resource(), we don't know its groups without querying Metabase,
        # which we don't need to do when going through this method.
        self.assertEqual("<Unknown>", user.groups)

        self.assertEqual(user.resource, metabase_user)

    def test_create(self):
        """Ensure User.create() calls metabase.User.create() and metabase.User.send_invite()."""
        metabase_user = metabase.User(
            id=1,
            email="my_email",
            first_name="my_first_name",
            last_name="my_last_name",
            _using=None,
        )
        with patch.object(metabase.User, "create", return_value=metabase_user) as u:
            with patch.object(metabase.User, "send_invite") as send_invite:
                user = User(
                    email="my_email",
                    first_name="my_first_name",
                    last_name="my_last_name",
                )
                user.create(using=None)

                self.assertTrue(u.called)
                self.assertTrue(send_invite.called)

    def test_create_reactivate(self):
        """Ensure User.create() calls .reactivate() when the email points to a deactivated user."""
        metabase_user = metabase.User(
            id=1,
            email="reactivate@example.com",
            first_name="my_first_name",
            last_name="my_last_name",
            _using=None,
        )

        with patch.object(
            metabase.User,
            "create",
            side_effect=HTTPError(
                '{"error": {"message": "Email address already in use."}}'
            ),
        ) as u:
            with patch.object(metabase.User, "list", return_value=[metabase_user]) as l:
                with patch.object(metabase.User, "reactivate") as r:
                    user = User(
                        email="reactivate@example.com",
                        first_name="my_first_name",
                        last_name="my_last_name",
                    )
                    user.create(using=None)

                    self.assertTrue(l.called)
                    self.assertTrue(r.called)

    def test_update(self):
        """Ensure User.update() calls update() on the provided class."""
        with patch.object(metabase.User, "update") as c:
            metabase_user = metabase.User(
                email="not_my_email",
                first_name="my_first_name",
                last_name="my_last_name",
                _using=None,
            )
            user = User(
                email="my_email", first_name="my_first_name", last_name="my_last_name", resource=metabase_user
            )
            user.update()

            self.assertIsNone(
                c.assert_called_with(
                    first_name="my_first_name",
                    last_name="my_last_name",
                    email="my_email",
                )
            )

    def test_delete(self):
        """Ensure User.delete() calls delete() on the provided class."""
        with patch.object(metabase.User, "delete") as c:
            metabase_user = metabase.User(
                email="not_my_email",
                first_name="my_first_name",
                last_name="my_last_name",
                _using=None,
            )
            user = User(
                email="my_email", first_name="my_first_name", last_name="my_last_name", resource=metabase_user
            )
            user.delete()

            self.assertTrue(c.called)
