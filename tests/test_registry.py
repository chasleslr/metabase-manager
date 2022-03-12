from metabase import Database, Field, Metric, Segment, Table, User

from tests.helpers import IntegrationTestCase

from metabase_manager.registry import MetabaseRegistry


class MetabaseTests(IntegrationTestCase):
    def test_cache_databases(self):
        """Ensure MetabaseRegistry.cache_databases() saves all databases to the instance."""
        registry = MetabaseRegistry(client=self.metabase)

        registry.cache_databases()
        self.assertIsInstance(registry.databases, list)
        self.assertIsInstance(next(iter(registry.databases)), Database)

    def test_cache_tables(self):
        """Ensure MetabaseRegistry.cache_tables() saves all tables to the instance."""
        registry = MetabaseRegistry(client=self.metabase)

        registry.cache_tables()
        self.assertIsInstance(registry.tables, list)
        self.assertIsInstance(next(iter(registry.tables)), Table)

    def test_cache_users(self):
        """Ensure MetabaseRegistry.cache_users() saves all users to the instance."""
        registry = MetabaseRegistry(client=self.metabase)

        registry.cache_users()
        self.assertIsInstance(registry.users, list)
        self.assertIsInstance(next(iter(registry.users)), User)

    def test_cache_fields(self):
        """Ensure MetabaseRegistry.cache_fields() saves all fields to the instance."""
        registry = MetabaseRegistry(client=self.metabase)

        registry.cache_tables()
        registry.cache_fields()
        self.assertIsInstance(registry.fields, list)
        self.assertIsInstance(next(iter(registry.fields)), Field)

    def test_get_database(self):
        """Ensure MetabaseRegistry.get_database() returns a Database by ID."""
        db1 = Database(id=1, _using=self.metabase)
        db2 = Database(id=2, _using=self.metabase)
        registry = MetabaseRegistry(databases=[db1, db2], client=self.metabase)

        self.assertEqual(db1, registry.get_database(1))
        self.assertEqual(db2, registry.get_database(2))

    def test_get_table(self):
        """Ensure MetabaseRegistry.get_table() returns a Table by ID."""
        table1 = Table(id=1, _using=self.metabase)
        table2 = Table(id=2, _using=self.metabase)
        registry = MetabaseRegistry(tables=[table1, table2], client=self.metabase)

        self.assertEqual(table1, registry.get_table(1))
        self.assertEqual(table2, registry.get_table(2))

    def test_get_field(self):
        """Ensure MetabaseRegistry.get_field() returns a Field by ID."""
        field1 = Field(id=1, _using=self.metabase)
        field2 = Field(id=2, _using=self.metabase)
        registry = MetabaseRegistry(fields=[field1, field2], client=self.metabase)

        self.assertEqual(field1, registry.get_field(1))
        self.assertEqual(field2, registry.get_field(2))

    def test_get_user(self):
        """Ensure MetabaseRegistry.get_user() returns a User by ID."""
        user1 = User(id=1, _using=self.metabase)
        user2 = User(id=2, _using=self.metabase)
        registry = MetabaseRegistry(users=[user1, user2], client=self.metabase)

        self.assertEqual(user1, registry.get_user(1))
        self.assertEqual(user2, registry.get_user(2))

    def test_get_metric(self):
        """Ensure MetabaseRegistry.get_metric() returns a Metric by ID."""
        metric1 = Metric(id=1, _using=self.metabase)
        metric2 = Metric(id=2, _using=self.metabase)
        registry = MetabaseRegistry(metrics=[metric1, metric2], client=self.metabase)

        self.assertEqual(metric1, registry.get_metric(1))
        self.assertEqual(metric2, registry.get_metric(2))

    def test_get_segment(self):
        """Ensure MetabaseRegistry.get_segment() returns a Segment by ID."""
        segment1 = Segment(id=1, _using=self.metabase)
        segment2 = Segment(id=2, _using=self.metabase)
        registry = MetabaseRegistry(segments=[segment1, segment2], client=self.metabase)

        self.assertEqual(segment1, registry.get_segment(1))
        self.assertEqual(segment2, registry.get_segment(2))
