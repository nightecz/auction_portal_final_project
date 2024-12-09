import os
import django
from django.test import TestCase
from django.urls import reverse

os.environ['DJANGO_SETTINGS_MODULE'] = 'final_project.settings'
django.setup()

class IndexViewTest(TestCase):
    def test_index_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)