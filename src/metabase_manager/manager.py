from dataclasses import dataclass
from typing import Dict, List, Tuple, Type

from metabase import Metabase
from metabase.resource import DeleteResource, Resource

from metabase_manager.entities import Entity, User
from metabase_manager.exceptions import DuplicateKeyError
from metabase_manager.parser import MetabaseParser
from metabase_manager.registry import MetabaseRegistry


@dataclass
class MetabaseManager:
    registry: MetabaseRegistry
    config: MetabaseParser

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

    @staticmethod
    def find_objects_to_create(
        metabase: Dict[str, Resource],
        config: Dict[str, Entity],
    ) -> List[Entity]:
        return [config[key] for key in config.keys() - metabase.keys()]

    @staticmethod
    def find_objects_to_update(
        metabase: Dict[str, Resource],
        config: Dict[str, Entity],
    ) -> List[Tuple[Resource, Entity]]:
        return [
            (metabase[key], config[key])
            for key in metabase.keys() & config.keys()
            if not config[key].is_equal(metabase[key])
        ]

    @staticmethod
    def find_objects_to_delete(
        metabase: Dict[str, Resource],
        config: Dict[str, Entity],
    ) -> List[Resource]:
        return [metabase[key] for key in metabase.keys() - config.keys()]

    @staticmethod
    def create(objects: List[Entity], using: Metabase):
        for obj in objects:
            obj.create(using=using)

    @staticmethod
    def update(objects: List[Tuple[Resource, Entity]]):
        for metabase, config in objects:
            config.update(metabase)

    @staticmethod
    def delete(objects: List[DeleteResource]):
        for obj in objects:
            obj.delete()
