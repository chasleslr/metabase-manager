import subprocess
from unittest import TestCase

import requests
from metabase import Database, Metabase, PermissionGroup, User


class IntegrationTestCase(TestCase):
    HOST = "http://0.0.0.0:3000"
    FIRST_NAME = "test"
    LAST_NAME = "test"
    EMAIL = "test@example.com"
    PASSWORD = "example123"
    SITE_NAME = "metabase-python"

    @classmethod
    def setUpClass(cls) -> None:
        cls.setup_metabase()

    def setUp(self) -> None:
        self.metabase = Metabase(
            host=self.HOST, user=self.EMAIL, password=self.PASSWORD
        )

    @classmethod
    def tearDownClass(cls) -> None:
        # remove all databases created as fixtures
        metabase = Metabase(host=cls.HOST, user=cls.EMAIL, password=cls.PASSWORD)
        databases = Database.list(using=metabase)

        for database in databases:
            if database.name != "Sample Database":
                database.delete()

        for user in User.list(using=metabase):
            if user.email != cls.EMAIL:
                user.delete()

        for group in PermissionGroup.list(using=metabase):
            if group.name not in ["All Users", "Administrators"]:
                group.delete()

    @classmethod
    def setup_metabase(cls):
        response = requests.get(cls.HOST + "/api/session/properties")
        token = response.json()["setup-token"]

        if token is not None:
            response = requests.post(
                cls.HOST + "/api/setup",
                json={
                    "prefs": {"site_name": cls.SITE_NAME},
                    "user": {
                        "email": cls.EMAIL,
                        "password": cls.PASSWORD,
                        "first_name": cls.FIRST_NAME,
                        "last_name": cls.LAST_NAME,
                        "site_name": cls.SITE_NAME,
                    },
                    "token": token,
                },
            )
