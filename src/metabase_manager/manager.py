from dataclasses import InitVar, dataclass, field
from typing import Dict, List, Type

from metabase import Metabase
from metabase.resource import Resource

from metabase_manager.entities import Entity, Group, User
from metabase_manager.exceptions import DuplicateKeyError
from metabase_manager.parser import MetabaseParser
from metabase_manager.registry import MetabaseRegistry


@dataclass
class MetabaseManager:
    metabase_host: InitVar[str]
    metabase_user: InitVar[str]
    metabase_password: InitVar[str]

    select: List[str] = field(default_factory=list)
    exclude: List[str] = field(default_factory=list)

    client: Metabase = None
    registry: MetabaseRegistry = None
    config: MetabaseParser = None

    # objects are managed in the same order as the dictionary keys
    _entities = {
        "groups": Group,
        "users": User,
    }

    def __post_init__(self, metabase_host, metabase_user, metabase_password):
        self.client = Metabase(
            host=metabase_host, user=metabase_user, password=metabase_password
        )

    @classmethod
    def get_allowed_keys(cls) -> List[str]:
        return list(cls._entities.keys())

    def get_entities_to_manage(self) -> List[Type[Entity]]:
        select = self.select or self.get_allowed_keys()
        return [
            self._entities[key]
            for key in self.get_allowed_keys()
            if key in set(select).difference(self.exclude)
        ]

    def parse_config(self, paths: List[str]):
        self.config = MetabaseParser.from_paths(paths)

    def cache_metabase(self):
        self.registry = MetabaseRegistry(client=self.client)
        self.registry.cache(self.select, self.exclude)

    def get_metabase_objects(self, obj: Type[Entity]) -> Dict[str, Resource]:
        metabase = {}
        for instance in self.registry.get_instances_for_object(obj.METABASE):
            key = obj.get_key_from_metabase_instance(instance)

            if key in metabase:
                raise DuplicateKeyError()

            metabase[key] = instance

        return metabase

    def get_config_objects(self, obj: Type[Entity]) -> Dict[str, Entity]:
        config = {}
        for instance in self.config.get_instances_for_object(obj):
            if instance.key in config:
                raise DuplicateKeyError()

            config[instance.key] = instance

        return config

    def find_objects_to_create(self, obj: Type[Entity]) -> List[Entity]:
        config = self.get_config_objects(obj)
        metabase = self.get_metabase_objects(obj)

        entities = []
        for key in config.keys() - metabase.keys():
            entity = config[key]
            entity.registry = self.registry
            entities.append(entity)

        return entities

    def find_objects_to_update(self, obj: Type[Entity]) -> List[Entity]:
        config = self.get_config_objects(obj)
        metabase = self.get_metabase_objects(obj)

        entities = []
        for key in metabase.keys() & config.keys():
            entity = config[key]
            entity.registry = self.registry
            if not entity.is_equal(metabase[key]):
                entity.resource = metabase[key]
                entities.append(entity)

        return entities

    def find_objects_to_delete(self, obj: Type[Entity]) -> List[Entity]:
        config = self.get_config_objects(obj)
        metabase = self.get_metabase_objects(obj)

        return [
            obj.from_resource(resource=metabase[key])
            for key in metabase.keys() - config.keys()
            if obj.can_delete(metabase[key])
        ]

    def create(self, entity: Entity):
        entity.create(using=self.client)

    def update(self, entity: Entity):
        entity.update()

    def delete(self, entity: Entity):
        entity.delete()
