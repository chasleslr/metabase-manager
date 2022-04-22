from dataclasses import dataclass, field
from typing import List, Optional, Type

import metabase
from metabase import (
    Database,
    Field,
    Metabase,
    Metric,
    PermissionGroup,
    Segment,
    Table,
    User,
)
from metabase.resource import Resource

from metabase_manager.exceptions import DuplicateKeyError


@dataclass
class MetabaseRegistry:
    client: Metabase

    databases: List[Database] = field(default_factory=list)
    tables: List[Table] = field(default_factory=list)
    users: List[User] = field(default_factory=list)
    groups: List[PermissionGroup] = field(default_factory=list)
    fields: List[Field] = field(default_factory=list)
    metrics: List[Metric] = field(default_factory=list)
    segments: List[Segment] = field(default_factory=list)

    _REGISTRY = {
        "groups": PermissionGroup,
        "users": User,
        "databases": Database,
        "tables": Table
    }

    @classmethod
    def get_registry_keys(cls) -> List[str]:
        return list(cls._REGISTRY.keys())

    def test(self):
        databases = Database.list(using=self.client)
        tables = [table for db in databases for schema in db.schemas() for table in db.tables(schema)]

        for table in tables:
            print(table.name, table.display_name, table.description)

    def cache(self, select: List[str] = None, exclude: List[str] = None):
        if not select:
            select = self.get_registry_keys()

        if exclude is None:
            exclude = {}

        for key in set(select).difference(set(exclude)):
            # call .list() method on objects in self._MAPPING for every
            # key in `select` not in `exclude, and set attribute
            setattr(self, key, self._REGISTRY[key].list(using=self.client))

    def get_instances_for_object(self, obj: Type[Resource]) -> List[Resource]:
        if obj == User:
            return self.users
        if obj == PermissionGroup:
            return self.groups
        if obj == Table:
            return self.tables
        raise NotImplementedError(f"{obj.__name__} is not implemented in {self.__class__.__name__}")

    def get_group_by_name(self, name: str) -> Optional[metabase.PermissionGroup]:
        groups = list(filter(lambda g: g.name == name, self.groups))

        if len(groups) > 1:
            raise DuplicateKeyError(
                f"Found more than one group with the same name: {name}"
            )

        return next(iter(groups), None)
