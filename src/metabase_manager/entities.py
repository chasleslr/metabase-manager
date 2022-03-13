from dataclasses import dataclass, field
from typing import List, Type
from uuid import uuid4

import metabase
from metabase.resource import Resource
from requests import HTTPError


class Entity:
    METABASE: Type[Resource]

    @classmethod
    def load(cls, config: dict):
        return cls(**config)

    @property
    def key(self) -> str:
        raise NotImplementedError

    @staticmethod
    def get_key_from_metabase_instance(instance: Resource) -> str:
        raise NotImplementedError

    def is_equal(self, resource: Resource) -> bool:
        raise NotImplementedError

    def create(self, using: metabase.Metabase):
        """Create an Entity in Metabase based on the config definition."""
        raise NotImplementedError

    def update(self, instance: Resource):
        """Update an Entity in Metabase based on the config definition."""
        raise NotImplementedError

    def delete(self, instance: Resource):
        """Delete an Entity in Metabase based on the config definition."""
        raise NotImplementedError


@dataclass
class Group(Entity):
    METABASE = metabase.PermissionGroup
    _PROTECTED_GROUPS = ["All Users", "Administrators"]

    name: str

    @property
    def key(self) -> str:
        return self.name

    def is_equal(self, group: metabase.PermissionGroup) -> bool:
        if self.name == group.name:
            return True
        return False

    @staticmethod
    def get_key_from_metabase_instance(instance: metabase.PermissionGroup) -> str:
        return instance.name

    def create(self, using: metabase.Metabase):
        metabase.PermissionGroup.create(using=using, name=self.name)

    def update(self, instance: metabase.PermissionGroup):
        # PermissionGroup should not be updated given the only attribute is the key
        pass

    def delete(self, instance: metabase.PermissionGroup):
        # some groups are protected and can not be deleted
        if instance.name not in self._PROTECTED_GROUPS:
            instance.delete()


@dataclass
class User(Entity):
    METABASE = metabase.User

    first_name: str
    last_name: str
    email: str
    groups: List[Group] = field(default_factory=list)

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
    def get_key_from_metabase_instance(instance: metabase.User) -> str:
        return instance.email

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

    def update(self, instance: metabase.User):
        instance.update(
            first_name=self.first_name,
            last_name=self.last_name,
            email=self.email,
        )

    def delete(self, instance: metabase.User):
        instance.delete()
