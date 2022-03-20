from dataclasses import dataclass
from random import random
from unittest import TestCase
from unittest.mock import PropertyMock, patch

import metabase
from metabase import PermissionGroup

from metabase_manager.entities import Entity, Group, User
from metabase_manager.exceptions import NotFoundError
from metabase_manager.registry import MetabaseRegistry
from tests.helpers import IntegrationTestCase


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

    def test_resource(self):
        with patch.object(Entity, "get_key_from_metabase_instance", return_value="two"):
            with patch.object(Entity, "key", new_callable=PropertyMock) as key:
                key.return_value = "two"
                entity = Entity()
                # no errors are raised
                entity.resource = "two"
                self.assertEqual("two", entity.resource)

        with patch.object(Entity, "get_key_from_metabase_instance", return_value="two"):
            with patch.object(Entity, "key", new_callable=PropertyMock):
                key.return_value = "one"
                with self.assertRaises(ValueError):
                    entity = Entity()
                    entity.resource = ""

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


class GroupTests(IntegrationTestCase):
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
        self.assertFalse(
            group.can_delete(PermissionGroup(name="All Users", _using=None))
        )
        self.assertFalse(
            group.can_delete(PermissionGroup(name="Administrators", _using=None))
        )

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
        group = Group(name="my_group")
        group.create(using=self.metabase)

        # get group from Metabase to check attributes
        groups = metabase.PermissionGroup.list(using=self.metabase)
        metabase_group = next(filter(lambda g: g.name == group.name, groups))

        self.assertEqual(group.name, metabase_group.name)

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
        group = Group(name=str(random()))

        # create group and ensure it exists
        group.create(using=self.metabase)
        groups = metabase.PermissionGroup.list(using=self.metabase)
        metabase_group = next(filter(lambda g: g.name == group.name, groups))
        self.assertEqual(group.name, metabase_group.name)

        # delete and ensure it does not exist
        group.resource = metabase_group
        group.delete()
        groups = metabase.PermissionGroup.list(using=self.metabase)
        self.assertFalse(group.name in [g.name for g in groups])

    def test_delete_protected(self):
        """
        Ensure Group.delete() does not call delete() on the provided
        class if the name is in self._PROTECTED_GROUPS.
        """
        with patch.object(metabase.PermissionGroup, "delete") as c:
            group = Group(
                name="my_group",
                _resource=metabase.PermissionGroup(name="All Users", _using=None),
            )
            group.delete()

            self.assertFalse(c.called)


class UserTests(IntegrationTestCase):
    def test_load(self):
        """Ensure User.load() returns an instance of User."""
        config = {
            "first_name": "user",
            "last_name": "one",
            "email": "user1@example.com",
            "groups": ["Administrators", "Developers"],
        }
        user = User.load(config)

        self.assertIsInstance(user, User)
        self.assertEqual(user.first_name, config["first_name"])
        self.assertEqual(user.last_name, config["last_name"])
        self.assertEqual(user.email, config["email"])
        self.assertIsInstance(user.groups, list)
        self.assertEqual(user.groups[0].name, "Administrators")
        self.assertEqual(user.groups[1].name, "Developers")

    def test_key(self):
        """Ensure User.key returns its name."""
        user = User(
            email="my_email", first_name="my_first_name", last_name="my_last_name"
        )
        self.assertEqual("my_email", user.key)

    def test_group_ids(self):
        """Ensure User.group_ids returns a list of integer matching the IDs of the PermissionGroups in the registry/"""
        registry = MetabaseRegistry(
            client=self.metabase,
            groups=[
                PermissionGroup(id=2, name="Administrators", _using=None),
                PermissionGroup(id=3, name="Developers", _using=None),
                PermissionGroup(id=5, name="Read-Only", _using=None),
            ],
        )

        user = User(
            email="my_email",
            first_name="my_first_name",
            last_name="my_last_name",
            groups=[
                Group(name="Read-Only"),
                Group(name="Administrators"),
                Group(name="Unknown"),
            ],
            registry=registry,
        )

        # 1 is appended at the end
        # Unknown is replaced with -1
        self.assertEqual([5, 2, -1, 1], user.group_ids)

        user = User(
            email="my_email",
            first_name="my_first_name",
            last_name="my_last_name",
            groups=[],
            registry=registry,
        )

        # 1 is appended at the end
        self.assertEqual([1], user.group_ids)

    def test_is_equal(self):
        """Ensure User.is_equal() returns True if a metabase.User has the same name."""
        registry = MetabaseRegistry(
            client=self.metabase,
            groups=[
                PermissionGroup(id=2, name="Administrators", _using=None),
                PermissionGroup(id=3, name="Developers", _using=None),
                PermissionGroup(id=5, name="Read-Only", _using=None),
            ],
        )

        test_matrix = [
            (
                User(
                    email="my_email",
                    first_name="my_first_name",
                    last_name="my_last_name",
                    groups=[],
                    registry=registry,
                ),
                metabase.User(
                    email="my_email",
                    first_name="my_first_name",
                    last_name="my_last_name",
                    group_ids=[1],
                    _using=None,
                ),
                True,
            ),
            (
                User(
                    email="my_email",
                    first_name="my_first_name",
                    last_name="my_last_name",
                ),
                metabase.User(
                    email="wrong",
                    first_name="my_first_name",
                    last_name="my_last_name",
                    group_ids=[1],
                    _using=None,
                ),
                False,
            ),
            (
                User(
                    email="my_email",
                    first_name="my_first_name",
                    last_name="my_last_name",
                ),
                metabase.User(
                    email="my_email",
                    first_name="wrong",
                    last_name="my_last_name",
                    group_ids=[1],
                    _using=None,
                ),
                False,
            ),
            (
                User(
                    email="my_email",
                    first_name="my_first_name",
                    last_name="my_last_name",
                ),
                metabase.User(
                    email="my_email",
                    first_name="my_first_name",
                    last_name="wrong",
                    group_ids=[1],
                    _using=None,
                ),
                False,
            ),
            (
                User(
                    email="my_email",
                    first_name="my_first_name",
                    last_name="my_last_name",
                    groups=[Group(name="Administrators")],
                ),
                metabase.User(
                    email="wrong",
                    first_name="my_first_name",
                    last_name="my_last_name",
                    group_ids=[1],
                    _using=None,
                ),
                False,
            ),
        ]

        for user, metabase_user, expected in test_matrix:
            self.assertEqual(expected, user.is_equal(metabase_user))

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
            _using=None,
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
        """Ensure User.create() successfully creates a User in Metabase with all defined attributes."""
        registry = MetabaseRegistry(client=self.metabase)
        registry.cache(select=["users", "groups"])

        test_matrix = [
            User(
                first_name="User",
                last_name="One",
                email=f"{random()}@example.com",
                groups=[],
                registry=registry,
            ),
            User(
                first_name="User",
                last_name="Two",
                email=f"{random()}@example.com",
                groups=[Group(name="Administrators"), Group(name="All Users")],
                registry=registry,
            ),
        ]

        for user in test_matrix:
            # assert user does not already exist
            self.assertListEqual(
                [], metabase.User.list(using=self.metabase, query=user.email)
            )

            user.create(using=self.metabase)

            # get user from Metabase to check attributes
            users = metabase.User.list(using=self.metabase, query=user.email)
            self.assertEqual(1, len(users))
            self.assertEqual(user.first_name, users[0].first_name)
            self.assertEqual(user.last_name, users[0].last_name)
            self.assertEqual(user.email, users[0].email)
            self.assertSetEqual(set(user.group_ids), set(users[0].group_ids))

    def test_create_invalid_group(self):
        """Ensure User.create() raises NotFoundError when it is part of a group that does not exist in Metabase."""
        registry = MetabaseRegistry(client=self.metabase)
        registry.cache(select=["users", "groups"])

        user = User(
            first_name="User",
            last_name="One",
            email=f"{random()}@example.com",
            groups=[Group("New Group")],
            registry=registry,
        )

        with self.assertRaises(NotFoundError):
            user.create(using=self.metabase)

    def test_create_calls_send_invite(self):
        """Ensure User.create() calls metabase.User.send_invite()."""
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
        """Ensure User.create() reactivates a user when it already existed and was deactivated."""
        registry = MetabaseRegistry(client=self.metabase)
        registry.cache(select=["users", "groups"])

        user = User(
            first_name="User",
            last_name="One",
            email=f"{random()}@example.com",
            groups=[],
            registry=registry,
        )

        # create mock user in Metabase
        user.create(using=self.metabase)

        # confirm it was created
        metabase_user = metabase.User.list(using=self.metabase, query=user.email)[0]
        self.assertEqual(user.email, metabase_user.email)

        # deactivate it and confirm it was reflected in Metabase
        metabase_user.delete()
        self.assertEqual([], metabase.User.list(using=self.metabase, query=user.email))

        # update an attribute, create, and expect user to be reactivated with the new attribute
        user.last_name = "Two"
        user.create(using=self.metabase)

        metabase_user = metabase.User.list(using=self.metabase, query=user.email)[0]
        self.assertEqual(user.email, metabase_user.email)
        self.assertEqual("Two", metabase_user.last_name)

    def test_update(self):
        """Ensure User.update() updates all attributes of a user in Metabase."""
        registry = MetabaseRegistry(client=self.metabase)
        registry.cache(select=["users", "groups"])

        user = User(
            first_name="User",
            last_name="One",
            email=f"{random()}@example.com",
            groups=[],
            registry=registry,
        )

        # create mock user in Metabase
        user.create(using=self.metabase)

        # confirm it was created
        metabase_user = metabase.User.list(using=self.metabase, query=user.email)[0]
        self.assertEqual(user.email, metabase_user.email)
        self.assertEqual(1, len(metabase_user.group_ids))

        # change attributes, update, and expect user to be updated in Metabase
        user.resource = metabase_user
        user.first_name = "user"
        user.last_name = "two"
        user.groups = [Group("Administrators")]
        user.update()

        metabase_user = metabase.User.list(using=self.metabase, query=user.email)[0]
        self.assertEqual(user.email, metabase_user.email)
        self.assertEqual("user", metabase_user.first_name)
        self.assertEqual("two", metabase_user.last_name)
        self.assertEqual(2, len(metabase_user.group_ids))

    def test_delete(self):
        """Ensure User.delete() calls delete() on the provided class."""
        user = User(
            first_name="User",
            last_name="One",
            email=f"{random()}@example.com",
            groups=[],
        )
        user.create(using=self.metabase)

        # confirm it was created
        metabase_user = metabase.User.list(using=self.metabase, query=user.email)[0]
        self.assertEqual(user.email, metabase_user.email)

        user.resource = metabase_user
        user.delete()

        # confirm it was deleted
        self.assertEqual([], metabase.User.list(using=self.metabase, query=user.email))

    def test_validate_groups(self):
        """Ensure User.validate_groups() raises a NotFoundError when -1 is part of the list."""
        user = User(
            first_name="User",
            last_name="One",
            email=f"{random()}@example.com",
            groups=[],
        )

        # should not raise error
        user.validate_groups()

        # should not raise error
        with patch.object(User, "group_ids", new_callable=PropertyMock) as group_ids:
            group_ids.return_value = [1, 2, 3]
            user.validate_groups()

        with self.assertRaises(NotFoundError):
            with patch.object(
                User, "group_ids", new_callable=PropertyMock
            ) as group_ids:
                user.groups = [
                    Group(name="Group1"),
                    Group(name="Group2"),
                    Group(name="Group3"),
                ]
                group_ids.return_value = [1, -1, 3]
                user.validate_groups()
