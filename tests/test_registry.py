from unittest.mock import patch

from metabase import PermissionGroup, User

from metabase_manager.exceptions import DuplicateKeyError
from metabase_manager.registry import MetabaseRegistry
from tests.helpers import IntegrationTestCase


class MetabaseRegistryTests(IntegrationTestCase):
    def test_get_registry_keys(self):
        """Ensure MetabaseRegistry.get_registry_keys() returns all keys in cls._REGISTRY."""
        registry = MetabaseRegistry(client=None)

        self.assertListEqual(["groups", "users"], registry.get_registry_keys())

    def test_cache(self):
        """Ensure MetabaseRegistry.cache() sets all a"""
        registry = MetabaseRegistry(client=None)

        users = [User(_using=None), User(_using=None)]
        groups = [PermissionGroup(_using=None), PermissionGroup(_using=None)]

        with patch.object(User, "list", return_value=users) as user:
            with patch.object(PermissionGroup, "list", return_value=groups) as group:
                registry.cache()

                self.assertTrue(user.called)
                self.assertTrue(group.called)

                self.assertEqual(users, registry.users)
                self.assertEqual(groups, registry.groups)

        with patch.object(User, "list") as user:
            with patch.object(PermissionGroup, "list") as group:
                registry.cache(select=["users"])

                self.assertTrue(user.called)
                self.assertFalse(group.called)

        with patch.object(User, "list") as user:
            with patch.object(PermissionGroup, "list") as group:
                registry.cache(exclude=["users"])

                self.assertFalse(user.called)
                self.assertTrue(group.called)

        with patch.object(User, "list") as user:
            with patch.object(PermissionGroup, "list") as group:
                registry.cache(select=["users", "groups"], exclude=["users", "groups"])

                self.assertFalse(user.called)
                self.assertFalse(group.called)

        with patch.object(User, "list", return_value=users) as user:
            with patch.object(PermissionGroup, "list", return_value=groups) as group:
                registry.cache(select=None, exclude=None)

                self.assertTrue(user.called)
                self.assertTrue(group.called)

                self.assertEqual(users, registry.users)
                self.assertEqual(groups, registry.groups)

        with patch.object(User, "list", return_value=users) as user:
            with patch.object(PermissionGroup, "list", return_value=groups) as group:
                registry.cache(select=[], exclude=[])

                self.assertTrue(user.called)
                self.assertTrue(group.called)

                self.assertEqual(users, registry.users)
                self.assertEqual(groups, registry.groups)

    def test_get_instances_for_object(self):
        """
        Ensure MetabaseRegistry.get_instances_for_object() returns
        all instances in the registry for a given Resource.
        """
        registry = MetabaseRegistry(client=None)

        self.assertEqual([], registry.get_instances_for_object(User))
        self.assertEqual([], registry.get_instances_for_object(PermissionGroup))

        users = [User(_using=None), User(_using=None)]
        groups = [PermissionGroup(_using=None), PermissionGroup(_using=None)]
        registry.users = users
        registry.groups = groups

        self.assertEqual(users, registry.get_instances_for_object(User))
        self.assertEqual(groups, registry.get_instances_for_object(PermissionGroup))

    def test_get_group_by_name(self):
        """
        Ensure MetabaseRegistry.get_group_by_name() returns an instance of PermissionGroup
        if one exists with a matching name.
        """
        admin1 = PermissionGroup(id=1, name="Administrators", _using=None)
        admin2 = PermissionGroup(id=2, name="Administrators", _using=None)
        dev = PermissionGroup(id=3, name="Developers", _using=None)

        registry = MetabaseRegistry(client=None, groups=[admin1, admin2, dev])

        self.assertEqual(dev, registry.get_group_by_name("Developers"))
        self.assertIsNone(registry.get_group_by_name("unknown"))

        with self.assertRaises(DuplicateKeyError):
            registry.get_group_by_name("Administrators")
