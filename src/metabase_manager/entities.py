from dataclasses import dataclass, field
from typing import ClassVar, List, Type
from uuid import uuid4

import metabase
from metabase.resource import Resource
from requests import HTTPError

from metabase_manager.exceptions import NotFoundError
from metabase_manager.registry import MetabaseRegistry


class Entity:
    METABASE: ClassVar[Type[Resource]]
    _resource: Resource = field(default=None, repr=False)
    registry: MetabaseRegistry = field(default=None, repr=False)

    @classmethod
    def load(cls, config: dict):
        """Create an Entity from a dictionary."""
        return cls(**config)

    @property
    def key(self) -> str:
        """Unique key used to identify a matching Metabase Resource."""
        raise NotImplementedError

    @property
    def resource(self) -> Resource:
        return self._resource

    @resource.setter
    def resource(self, value):
        if self.key != self.get_key_from_metabase_instance(value):
            raise ValueError(
                f"Key mismatch between Entity and Resource: {self.key}, {self.get_key_from_metabase_instance(value)}"
            )

        self._resource = value

    @staticmethod
    def get_key_from_metabase_instance(resource: Resource) -> str:
        """
        Get the key from a Metabase Resource.
        Compared to Entity.key to find the Metabase Resource matching an Entity.
        """
        raise NotImplementedError

    @classmethod
    def from_resource(cls, resource: Resource) -> "Entity":
        """Create an instance of Entity from a Resource."""
        raise NotImplementedError

    @classmethod
    def can_delete(cls, resource: Resource) -> bool:
        """
        Whether a resource can be deleted if it is not found in the config.
        Some objects are protected and should never be deleted (i.e. Administrators group).
        """
        return True

    def is_equal(self, resource: Resource) -> bool:
        """
        Whether an Entity should be considered equal to a given Resource.
        Used to determine if a Resource should be updated.
        """
        raise NotImplementedError

    def create(self, using: metabase.Metabase):
        """Create an Entity in Metabase based on the config definition."""
        raise NotImplementedError

    def update(self):
        """Update an Entity in Metabase based on the config definition."""
        raise NotImplementedError

    def delete(self):
        """Delete an Entity in Metabase based on the config definition."""
        raise NotImplementedError


@dataclass
class Group(Entity):
    METABASE: ClassVar = metabase.PermissionGroup
    _PROTECTED: ClassVar = ["All Users", "Administrators"]

    name: str

    _resource: metabase.PermissionGroup = field(default=None, repr=False)

    @property
    def key(self) -> str:
        return self.name

    @Entity.resource.getter
    def resource(self) -> metabase.PermissionGroup:
        return self._resource

    def is_equal(self, group: metabase.PermissionGroup) -> bool:
        return True if self.name == group.name else False

    @classmethod
    def can_delete(cls, resource: metabase.PermissionGroup) -> bool:
        # some groups are protected and can not be deleted
        return True if resource.name not in cls._PROTECTED else False

    @staticmethod
    def get_key_from_metabase_instance(resource: metabase.PermissionGroup) -> str:
        return resource.name

    @classmethod
    def from_resource(cls, resource: metabase.PermissionGroup) -> "Group":
        return cls(name=resource.name, _resource=resource)

    def create(self, using: metabase.Metabase):
        metabase.PermissionGroup.create(using=using, name=self.name)

    def update(self):
        # PermissionGroup should not be updated given the only attribute is the key
        pass

    def delete(self):
        if self.can_delete(self.resource):
            self.resource.delete()


@dataclass
class User(Entity):
    METABASE: ClassVar = metabase.User

    first_name: str
    last_name: str
    email: str
    groups: List[Group] = field(default_factory=list)

    _resource: metabase.User = field(default=None, repr=False)
    registry: MetabaseRegistry = field(default=None, repr=False)

    @classmethod
    def load(cls, config: dict):
        """Create an Entity from a dictionary."""
        groups = config.pop("groups", []) or []
        return cls(groups=[Group(name=g) for g in groups], **config)

    @property
    def key(self) -> str:
        return self.email

    @Entity.resource.getter
    def resource(self) -> metabase.User:
        return self._resource

    @property
    def group_ids(self) -> List[int]:
        ids = []
        for group in self.groups:
            if permission_group := self.registry.get_group_by_name(group.name):
                ids.append(permission_group.id)
            else:
                # add placeholder
                # validate only on create/update to allow dry-run to succeed
                # (i.e. if a user is added to a new group as part of the same dry-run,
                # that group will not yet exist in Metabase)
                ids.append(-1)

        if 1 not in ids:
            # 'All Users' is always the first group and is mandatory
            ids.append(1)

        return ids

    def is_equal(self, user: metabase.User) -> bool:
        if (
            self.first_name == user.first_name
            and self.last_name == user.last_name
            and self.email == user.email
            and set(self.group_ids) == set(user.group_ids)
        ):
            return True
        return False

    @staticmethod
    def get_key_from_metabase_instance(resource: metabase.User) -> str:
        return resource.email

    @classmethod
    def from_resource(cls, resource: metabase.User) -> "User":
        return cls(
            first_name=resource.first_name,
            last_name=resource.last_name,
            email=resource.email,
            groups="<Unknown>",
            _resource=resource,
        )

    def create(self, using: metabase.Metabase):
        try:
            self.validate_groups()
            user = metabase.User.create(
                using=using,
                first_name=self.first_name,
                last_name=self.last_name,
                email=self.email,
                password=uuid4().hex,
                group_ids=self.group_ids,
            )
            user.send_invite()

        except HTTPError as e:
            if "Email address already in use." in str(e):
                self.resource = metabase.User.list(
                    using=using, query=self.email, include_deactivated=True
                )[0]
                self.resource.reactivate()
                # email already exists, but other attributes might differ
                self.update()
            else:
                raise e

    def update(self):
        self.validate_groups()
        self.resource.update(
            first_name=self.first_name,
            last_name=self.last_name,
            email=self.email,
            group_ids=self.group_ids,
        )

    def delete(self):
        self.resource.delete()

    def validate_groups(self):
        if -1 in self.group_ids:
            group = self.groups[self.group_ids.index(-1)]
            raise NotFoundError(
                f"User {self.email} is part of group {group.name} which could not be found in Metabase."
            )
