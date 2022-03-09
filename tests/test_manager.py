from unittest.mock import patch

import metabase

from metabase_manager.exceptions import DuplicateKeyError
from metabase_manager.manager import MetabaseManager
from metabase_manager.parser import MetabaseParser, User
from metabase_manager.registry import MetabaseRegistry
from tests.helpers import IntegrationTestCase


class ManagerTests(IntegrationTestCase):
    def test_get_metabase_objects(self):
        """
        Ensure MetabaseManager.get_metabase_objects() returns a dictionary with Resource
        as values, and keys from the matching Entity.get_key_from_metabase_instance.
        """
        user1 = metabase.User(
            id=1,
            email="my_email",
            first_name="my_first_name",
            last_name="my_last_name",
            _using=None,
        )
        registry = MetabaseRegistry(client=None, users=[user1])
        conf = MetabaseParser()
        manager = MetabaseManager(registry=registry, config=conf)

        self.assertDictEqual({"my_email": user1}, manager.get_metabase_objects(User))

    def test_get_metabase_objects_raises_duplicate(self):
        """
        Ensure MetabaseManager.get_metabase_objects() raises a DuplicateKeyError when
        more than one Resource with the same email exists..
        """
        user1 = metabase.User(
            id=1,
            email="my_email",
            first_name="my_first_name",
            last_name="my_last_name",
            _using=None,
        )
        user2 = metabase.User(
            id=2,
            email="my_email",
            first_name="my_first_name",
            last_name="my_last_name",
            _using=None,
        )

        registry = MetabaseRegistry(client=None, users=[user1, user2])
        conf = MetabaseParser()
        manager = MetabaseManager(registry=registry, config=conf)

        with self.assertRaises(DuplicateKeyError) as e:
            _ = manager.get_metabase_objects(User)

    def test_get_config_objects(self):
        """
        Ensure MetabaseManager.get_config_objects() returns a dictionary with Entity
        as values, and keys from the matching Entity.key.
        """
        user1 = User(
            email="my_email", first_name="my_first_name", last_name="my_last_name"
        )
        registry = MetabaseRegistry(client=None)
        conf = MetabaseParser(_users={"my_email": user1})
        manager = MetabaseManager(registry=registry, config=conf)

        self.assertDictEqual({"my_email": user1}, manager.get_config_objects(User))

    def test_get_config_objects_raises_duplicate(self):
        """
        Ensure MetabaseManager.get_config_objects() raises a DuplicateKeyError when
        more than one Entity with the same email exists.
        """
        user1 = User(
            email="my_email", first_name="my_first_name", last_name="my_last_name"
        )
        user2 = User(
            email="my_email", first_name="my_first_name", last_name="my_last_name"
        )
        registry = MetabaseRegistry(client=None)
        conf = MetabaseParser(_users={"my_email": user1, "my_email2": user2})
        manager = MetabaseManager(registry=registry, config=conf)

        with self.assertRaises(DuplicateKeyError) as e:
            _ = manager.get_config_objects(User)

    def test_find_objects_to_create(self):
        """
        Ensure MetabaseManager.find_objects_to_create() returns all Entity objects whose key
        is not found on Metabase.
        """
        registry = {
            "my_email": metabase.User(
                id=1,
                email="my_email",
                first_name="my_first_name",
                last_name="my_last_name",
                _using=None,
            )
        }
        config = {
            "not_my_email": User(
                email="not_my_email",
                first_name="my_first_name",
                last_name="my_last_name",
            ),
            "my_email": User(
                email="my_email", first_name="my_first_name", last_name="my_last_name"
            ),
        }

        out = MetabaseManager.find_objects_to_create(registry, config)

        self.assertIsInstance(out, list)
        self.assertEqual(1, len(out))
        self.assertEqual(out[0], config["not_my_email"])

    def test_find_objects_to_update(self):
        """
        Ensure MetabaseManager.find_objects_to_update() returns all Entity objects whose is_equal() method
        returns False for the Metabase resource matching its key.
        """
        registry = {
            "my_email": metabase.User(
                id=1,
                email="my_email",
                first_name="my_first_name",
                last_name="my_last_name",
                _using=None,
            )
        }
        config = {
            "not_my_email": User(
                email="not_my_email",
                first_name="my_first_name",
                last_name="my_last_name",
            ),
            "my_email": User(
                email="my_email",
                first_name="not_my_first_name",
                last_name="my_last_name",
            ),
        }

        out = MetabaseManager.find_objects_to_update(registry, config)

        self.assertIsInstance(out, list)
        self.assertEqual(1, len(out))
        self.assertIsInstance(out[0], tuple)
        self.assertEqual(out[0][0], registry["my_email"])
        self.assertEqual(out[0][1], config["my_email"])

    def test_find_objects_to_delete(self):
        """
        Ensure MetabaseManager.find_objects_to_delete() returns all Resource objects
        that are not defined in the config.
        """
        registry = {
            "my_email": metabase.User(
                id=1,
                email="my_email",
                first_name="my_first_name",
                last_name="my_last_name",
                _using=None,
            )
        }
        config = {
            "not_my_email": User(
                email="not_my_email",
                first_name="my_first_name",
                last_name="my_last_name",
            ),
        }

        out = MetabaseManager.find_objects_to_delete(registry, config)

        self.assertIsInstance(out, list)
        self.assertEqual(1, len(out))
        self.assertEqual(out[0], registry["my_email"])

    def test_create(self):
        """
        Ensure MetabaseManager.create() calls the .create() method on all
        object in the list of Resource.
        """
        with patch.object(User, "create") as create:
            users = [
                User(
                    email="my_email",
                    first_name="my_first_name",
                    last_name="my_last_name",
                ),
                User(
                    email="my_email",
                    first_name="my_first_name",
                    last_name="my_last_name",
                ),
            ]
            MetabaseManager.create(users, self.metabase)

            self.assertEqual(2, create.call_count)
            self.assertIsNone(create.assert_called_with(using=self.metabase))

    def test_update(self):
        """
        Ensure MetabaseManager.update() calls the .update() method on all
        object in the list of Resource.
        """
        with patch.object(User, "update") as update:
            users = [
                (
                    metabase.User(
                        id=1,
                        email="my_email",
                        first_name="my_first_name",
                        last_name="my_last_name",
                        _using=None,
                    ),
                    User(
                        email="my_email",
                        first_name="my_first_name",
                        last_name="my_last_name",
                    ),
                ),
                (
                    metabase.User(
                        id=2,
                        email="my_email",
                        first_name="my_first_name",
                        last_name="my_last_name",
                        _using=None,
                    ),
                    User(
                        email="my_email",
                        first_name="my_first_name",
                        last_name="my_last_name",
                    ),
                ),
            ]
            MetabaseManager.update(users)

            self.assertEqual(2, update.call_count)

    def test_delete(self):
        """
        Ensure MetabaseManager.delete() calls the .delete() method on all
        object in the list of Resource.
        """
        with patch.object(metabase.User, "delete") as delete:
            users = [
                metabase.User(
                    id=1,
                    email="my_email",
                    first_name="my_first_name",
                    last_name="my_last_name",
                    _using=None,
                ),
                metabase.User(
                    id=2,
                    email="my_email",
                    first_name="my_first_name",
                    last_name="my_last_name",
                    _using=None,
                ),
            ]
            MetabaseManager.delete(users)

            self.assertEqual(2, delete.call_count)
