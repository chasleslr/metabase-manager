from dataclasses import dataclass, field
from typing import List, Type
from uuid import uuid4

import metabase
from metabase.resource import Resource
from requests import HTTPError


class Entity:
    METABASE: Type[Resource]
    resource: Resource = field(default=None, repr=False)

    @classmethod
    def load(cls, config: dict):
        """Create an Entity from a dictionary."""
        return cls(**config)

    @property
    def key(self) -> str:
        """Unique key used to identify a matching Metabase Resource."""
        raise NotImplementedError

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
    METABASE = metabase.PermissionGroup
    _PROTECTED = ["All Users", "Administrators"]

    name: str

    resource: metabase.PermissionGroup = field(default=None, repr=False)

    @property
    def key(self) -> str:
        return self.name

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
        return cls(name=resource.name, resource=resource)

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
    METABASE = metabase.User

    first_name: str
    last_name: str
    email: str
    groups: List[Group] = field(default_factory=list)

    resource: metabase.User = field(default=None, repr=False)

    @property
    def key(self) -> str:
        return self.email

    def is_equal(self, user: metabase.User) -> bool:
        if (
            self.first_name == user.first_name
            and self.last_name == user.last_name
            and self.email == user.email
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
            resource=resource,
        )

    def create(self, using: metabase.Metabase):
        try:
            user = metabase.User.create(
                using=using,
                first_name=self.first_name,
                last_name=self.last_name,
                email=self.email,
                password=uuid4().hex,
            )
            user.send_invite()
        except HTTPError as e:
            if "Email address already in use." in str(e):
                users = metabase.User.list(
                    using=using, query=self.email, include_deactivated=True
                )
                users[0].reactivate()
            else:
                raise e

    def update(self):
        self.resource.update(
            first_name=self.first_name,
            last_name=self.last_name,
            email=self.email,
        )

    def delete(self):
        self.resource.delete()
