from faker import Faker
from rest_framework.test import APITestCase


class Gen:
    def __init__(self):
        self.faker = Faker()


class EAWorkTestCase(APITestCase):
    @classmethod
    def setUpClass(cls):
        cls.gen = Gen()
        super().setUpClass()
