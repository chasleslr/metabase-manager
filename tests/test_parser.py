import os
from pathlib import Path
from unittest import TestCase

from metabase_manager.parser import Group, MetabaseParser, User


class MetabaseParserTests(TestCase):
    def test_discover(self):
        """Ensure MetabaseParser.discover() returns all yaml files in a given directory and its subdirectories."""
        directory = os.path.join(os.path.dirname(__file__), "fixtures/metabase-manager")
        files = MetabaseParser.discover(directory)

        self.assertEqual(2, len(files))
        self.assertIsInstance(files[0], Path)

    def test_load_yaml(self):
        """Ensure MetabaseParser.load_yaml() opens and loads a yaml file into a dictionary."""
        filepath = os.path.join(os.path.dirname(__file__), "fixtures/metabase-manager/users.yaml")
        users = MetabaseParser.load_yaml(filepath)

        self.assertIsInstance(users, dict)

    def test_parse_yaml(self):
        """Ensure MetabaseParser.parse_yaml() registers all objects of all types in the yaml file."""
        # has both users and groups
        filepath = os.path.join(os.path.dirname(__file__), "fixtures/metabase-manager/users.yaml")
        objects = MetabaseParser.load_yaml(filepath)
        conf = MetabaseParser()

        self.assertEqual(0, len(conf.users))
        self.assertEqual(0, len(conf.groups))

        conf.parse_yaml(objects)

        self.assertEqual(1, len(conf.users))
        self.assertEqual(1, len(conf.groups))

    def test_register_objects(self):
        """Ensure MetabaseParser.register_objects() registers all objects of the same type in a list of dicts."""
        objects = [{"name": "Administrator"}, {"name": "Developers"}]
        conf = MetabaseParser()
        self.assertEqual(0, len(conf._groups.keys()))

        conf.register_objects(objects, "groups")

        self.assertEqual(2, len(conf._groups.keys()))
        self.assertIsInstance(conf._groups["Administrator"], Group)
        self.assertIsInstance(conf._groups["Developers"], Group)

    def test_register_object(self):
        """Ensure MetabaseParser.register_object() registers an object to the instance with the correct key."""
        user = User(first_name="", last_name="", email="foo")
        conf = MetabaseParser()

        conf.register_object(user, "users")
        self.assertEqual(conf._users["foo"], user)

    def test_register_object_raises_on_duplicate_key(self):
        """Ensure MetabaseParser.register_object() raises an error if the object_key already exists."""
        user = User(first_name="", last_name="", email="test@example.com")
        conf = MetabaseParser()

        conf.register_object(user, "users")

        with self.assertRaises(KeyError):
            conf.register_object(user, "users")
