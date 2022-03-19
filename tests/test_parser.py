import os
from pathlib import Path
from unittest import TestCase

from metabase_manager.exceptions import InvalidConfigError
from metabase_manager.parser import Group, MetabaseParser, User


class MetabaseParserTests(TestCase):
    def test_from_paths(self):
        """
        Ensure MetabaseParser.from_paths() returns an instance of MetabaseParser
        with registered config.
        """
        path_users = os.path.join(os.path.dirname(__file__), "fixtures/parser/users.yaml")
        path_groups = os.path.join(os.path.dirname(__file__), "fixtures/parser/subdirectory/groups.yml")

        parser = MetabaseParser.from_paths([path_users, path_groups])

        self.assertIsInstance(parser, MetabaseParser)
        self.assertSetEqual(
            {"Administrators", "Developers", "Read-Only"},
            set(parser._groups.keys())
        )
        self.assertSetEqual(
            {"test@test.com", "test@example.com"},
            set(parser._users.keys())
        )
        self.assertTrue(all([isinstance(u, User) for u in parser.users]))
        self.assertTrue(all([isinstance(g, Group) for g in parser.groups]))

    def test_load_yaml(self):
        """Ensure MetabaseParser.load_yaml() opens and loads a yaml file into a dictionary."""
        filepath = os.path.join(os.path.dirname(__file__), "fixtures/parser/users.yaml")
        users = MetabaseParser.load_yaml(filepath)

        self.assertIsInstance(users, dict)

    def test_parse_yaml(self):
        """Ensure MetabaseParser.parse_yaml() registers all objects of all types in the yaml file."""
        # has both users and groups
        filepath = os.path.join(os.path.dirname(__file__), "fixtures/parser/users.yaml")
        objects = MetabaseParser.load_yaml(filepath)
        conf = MetabaseParser()

        self.assertEqual(0, len(conf.users))
        self.assertEqual(0, len(conf.groups))

        conf.parse_yaml(objects)

        self.assertEqual(2, len(conf.users))
        self.assertEqual(1, len(conf.groups))

    def test_parse_yaml_raises_error(self):
        """Ensure MetabaseParser.parse_yaml() raises InvalidConfigError when unexpected keys are found."""
        parser = MetabaseParser()

        with self.assertRaises(InvalidConfigError):
            parser.parse_yaml({"unknown": {"something": ""}})

    def test_register_objects(self):
        """Ensure MetabaseParser.register_objects() registers all objects of the same type in a list of dicts."""
        objects = [{"name": "Administrators"}, {"name": "Developers"}]
        conf = MetabaseParser()
        self.assertEqual(0, len(conf._groups.keys()))

        conf.register_objects(objects, "groups")

        self.assertEqual(2, len(conf._groups.keys()))
        self.assertIsInstance(conf._groups["Administrators"], Group)
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
