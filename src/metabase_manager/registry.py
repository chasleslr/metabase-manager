from dataclasses import dataclass, field
from typing import List

from metabase import Database, Field, Metabase, Metric, Segment, Table, User


@dataclass
class MetabaseRegistry:
    client: Metabase

    databases: List[Database] = field(default_factory=list)
    tables: List[Table] = field(default_factory=list)
    users: List[User] = field(default_factory=list)
    fields: List[Field] = field(default_factory=list)
    metrics: List[Metric] = field(default_factory=list)
    segments: List[Segment] = field(default_factory=list)

    def cache_databases(self):
        """Find all Databases in Metabase and cache in the instance."""
        self.databases = Database.list(using=self.client)

    def cache_tables(self):
        """Find all Tables in Metabase and cache in the instance."""
        self.tables = Table.list(using=self.client)

    def cache_users(self):
        """Find all Users in Metabase and cache in the instance."""
        self.users = User.list(using=self.client)

    def cache_fields(self):
        """Find all Fields in Metabase and cache in the instance."""
        for table in self.tables:
            for field in table.fields():
                self.fields.append(field)

    def get_database(self, id: int) -> Database:
        """Get a Database by ID."""
        return next(filter(lambda db: db.id == id, self.databases))

    def get_table(self, id: int) -> Table:
        """Get a Table by ID."""
        return next(filter(lambda table: table.id == id, self.tables))

    def get_field(self, id: int) -> Field:
        """Get a Field by ID."""
        return next(filter(lambda field: field.id == id, self.fields))

    def get_user(self, id: int) -> User:
        """Get a User by ID."""
        return next(filter(lambda user: user.id == id, self.users))

    def get_metric(self, id: int) -> Metric:
        """Get a Metric by ID."""
        return next(filter(lambda metric: metric.id == id, self.metrics))

    def get_segment(self, id: int) -> Segment:
        """Get a Segment by ID."""
        return next(filter(lambda segment: segment.id == id, self.segments))
