from unittest import TestCase
from unittest.mock import patch

import metabase

from metabase_manager.entities import Group
from metabase_manager.exceptions import DuplicateKeyError
from metabase_manager.manager import MetabaseManager
from metabase_manager.parser import MetabaseParser, User
from metabase_manager.registry import MetabaseRegistry


class ManagerTests(TestCase):
    def test_get_allowed_keys(self):
        """Ensure MetabaseManager.get_allowed_keys() returns all keys in cls._entities."""
        manager = MetabaseManager(
            metabase_host=None, metabase_user=None, metabase_password=None
        )

        self.assertListEqual(["groups", "users"], manager.get_allowed_keys())

    def test_get_entities_to_manage(self):
        """
        Ensure MetabaseManager.get_entities_to_manage() returns a filtered list of Entity,
        in the same order as the keys in MetabaseManager._entities.
        """
        manager = MetabaseManager(
            metabase_host=None, metabase_user=None, metabase_password=None
        )
        self.assertListEqual([Group, User], manager.get_entities_to_manage())

        manager = MetabaseManager(
            select=["users"],
            metabase_host=None,
            metabase_user=None,
            metabase_password=None,
        )
        self.assertListEqual([User], manager.get_entities_to_manage())

        manager = MetabaseManager(
            select=["users", "groups"],
            metabase_host=None,
            metabase_user=None,
            metabase_password=None,
        )
        self.assertListEqual([Group, User], manager.get_entities_to_manage())

        manager = MetabaseManager(
            exclude=["users"],
            metabase_host=None,
            metabase_user=None,
            metabase_password=None,
        )
        self.assertListEqual([Group], manager.get_entities_to_manage())

    def test_parse_config(self):
        """Ensure MetabaseManager.parse_config() calls MetabaseParser.from_paths()."""
        manager = MetabaseManager(
            metabase_host=None, metabase_user=None, metabase_password=None
        )

        with patch.object(
            MetabaseParser, "from_paths", return_value=MetabaseParser()
        ) as from_paths:
            paths = ["path1", "path2"]
            manager.parse_config(paths=paths)

            self.assertIsNone(from_paths.assert_called_once_with(paths))
            self.assertIsInstance(manager.config, MetabaseParser)

    def test_cache_metabase(self):
        """Ensure MetabaseManager.cache_metabase() calls MetabaseRegistry"""
        manager = MetabaseManager(
            select=["users"],
            exclude=["groups"],
            metabase_host=None,
            metabase_user=None,
            metabase_password=None,
        )

        with patch.object(MetabaseRegistry, "cache") as cache:
            manager.cache_metabase()

            self.assertIsInstance(manager.registry, MetabaseRegistry)
            self.assertIsNone(cache.assert_called_once_with(["users"], ["groups"]))

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
        manager = MetabaseManager(
            registry=registry,
            config=conf,
            metabase_host=None,
            metabase_user=None,
            metabase_password=None,
        )

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
        manager = MetabaseManager(
            registry=registry,
            config=conf,
            metabase_host=None,
            metabase_user=None,
            metabase_password=None,
        )

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
        manager = MetabaseManager(
            registry=registry,
            config=conf,
            metabase_host=None,
            metabase_user=None,
            metabase_password=None,
        )

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
        manager = MetabaseManager(
            registry=registry,
            config=conf,
            metabase_host=None,
            metabase_user=None,
            metabase_password=None,
        )

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

        with patch.object(
            MetabaseManager, "get_config_objects", return_value=config
        ) as c:
            with patch.object(
                MetabaseManager, "get_metabase_objects", return_value=registry
            ) as r:
                manager = MetabaseManager(
                    metabase_host=None,
                    metabase_user=None,
                    metabase_password=None,
                    registry=registry,
                    config=config,
                )

                out = manager.find_objects_to_create(User)

                self.assertIsInstance(out, list)
                self.assertEqual(1, len(out))
                self.assertEqual(out[0], config["not_my_email"])
                self.assertEqual(out[0].registry, registry)

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

        with patch.object(
            MetabaseManager, "get_config_objects", return_value=config
        ) as c:
            with patch.object(
                MetabaseManager, "get_metabase_objects", return_value=registry
            ) as r:
                manager = MetabaseManager(
                    metabase_host=None,
                    metabase_user=None,
                    metabase_password=None,
                    registry=registry,
                    config=config,
                )

                out = manager.find_objects_to_update(User)

                self.assertIsInstance(out, list)
                self.assertEqual(1, len(out))
                self.assertEqual(out[0], config["my_email"])
                self.assertEqual(out[0].registry, registry)

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

        with patch.object(
            MetabaseManager, "get_config_objects", return_value=config
        ) as c:
            with patch.object(
                MetabaseManager, "get_metabase_objects", return_value=registry
            ) as r:
                manager = MetabaseManager(
                    metabase_host=None, metabase_user=None, metabase_password=None
                )

                out = manager.find_objects_to_delete(User)

                self.assertIsInstance(out, list)
                self.assertEqual(1, len(out))
                self.assertEqual(out[0], User.from_resource(registry["my_email"]))

    def test_create(self):
        """
        Ensure MetabaseManager.create() calls .create() method on a given Entity.
        """
        with patch.object(User, "create") as create:
            user = User(
                email="my_email",
                first_name="my_first_name",
                last_name="my_last_name",
            )

            manager = MetabaseManager(
                metabase_host=None, metabase_user=None, metabase_password=None
            )
            manager.create(user)

            self.assertIsNone(create.assert_called_with(using=manager.client))

    def test_update(self):
        """
        Ensure MetabaseManager.update() calls .update() method on a given Entity.
        """
        with patch.object(User, "update") as update:
            user = User(
                email="my_email",
                first_name="my_first_name",
                last_name="my_last_name",
            )

            manager = MetabaseManager(
                metabase_host=None, metabase_user=None, metabase_password=None
            )
            manager.update(user)

            self.assertTrue(update.called)

    def test_delete(self):
        """
        Ensure MetabaseManager.delete() calls .delete() method a given Entity.
        """
        with patch.object(User, "delete") as delete:
            user = User(
                email="my_email",
                first_name="my_first_name",
                last_name="my_last_name",
            )

            manager = MetabaseManager(
                metabase_host=None, metabase_user=None, metabase_password=None
            )
            manager.delete(user)

            self.assertTrue(delete.called)
