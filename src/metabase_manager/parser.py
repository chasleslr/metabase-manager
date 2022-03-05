from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Type, Union

import yaml


class ConfigObject:
    UNIQUE_ON: str

    @classmethod
    def load(cls, config: dict):
        return cls(**config)

    @property
    def key(self):
        return getattr(self, self.UNIQUE_ON)


@dataclass
class Group(ConfigObject):
    UNIQUE_ON = "name"

    name: str


@dataclass
class User(ConfigObject):
    UNIQUE_ON = "email"

    first_name: str
    last_name: str
    email: str
    groups: List[Group] = field(default_factory=list)


@dataclass
class MetabaseParser:
    users: Dict[str, User] = field(default_factory=dict)
    groups: Dict[str, Group] = field(default_factory=dict)

    _keys = {
        "users": User,
        "groups": Group
    }

    def register(self, directory: str):
        files = self.discover(directory)

        for file in files:
            loaded = self.load_yaml(file)
            self.parse_yaml(loaded)

    @staticmethod
    def discover(directory: str) -> List[Path]:
        """Discover YAML configuration files recursively in a directory."""
        files = []
        for ext in ('yaml', 'yml'):
            files.extend(Path(directory).rglob(f'*.{ext}'))
        return files

    @staticmethod
    def load_yaml(filepath: Union[str, Path]) -> dict:
        with open(filepath, "r") as f:
            return yaml.safe_load(f)

    def parse_yaml(self, yaml: dict):
        # iterate over keys in yaml file
        for key in yaml.keys():
            # only look for keys we want
            if key in self._keys.keys():
                # load every object defined this key (i.e. users, groups, etc.)
                self.register_objects(yaml[key], key)

    def register_objects(self, objects: List[dict], instance_key: str):
        cls = self._keys[instance_key]
        for obj in objects:
            self.register_object(cls.load(obj), instance_key)

    def register_object(self, obj: ConfigObject, instance_key: str):
        """Register an object to the instance."""
        registry = getattr(self, instance_key)

        if obj.key in registry:
            raise KeyError(f"Found more than one {obj.__class__.__name__} the same {obj.UNIQUE_ON}: {obj.key}.")

        registry[obj.key] = obj
