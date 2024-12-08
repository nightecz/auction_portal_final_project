from django.test import TestCase
from django.urls import reverse

class ViewTests(TestCase):
    def test_index_view(self):
        """
        Testuje, zda pohled `index` vrací správnou HTTP odpověď a používá správnou šablonu.
        """
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')

    def test_auctions_view(self):
        """
        Testuje, zda pohled `auctions` vrací správnou HTTP odpověď a používá správnou šablonu.
        """
        response = self.client.get(reverse('auctions'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'auctions.html')
