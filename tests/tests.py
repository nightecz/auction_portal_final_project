import os
import django
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

os.environ['DJANGO_SETTINGS_MODULE'] = 'final_project.settings'
django.setup()

#test for not logged user
class UrlsTests(TestCase):
    def test_urls(self):
        endpoints = [
            {'url': reverse('index'), 'name': 'index'},
            {'url': reverse('login'), 'name': 'login'},
            {'url': reverse('register'), 'name': 'register'},
            {'url': reverse('profile'), 'name': 'profile'},
            {'url': reverse('auctions'), 'name': 'auctions'},
            {'url': reverse('auction_create'), 'name': 'auction_create'},
        ]

        for endpoint in endpoints:
            with self.subTest(endpoint=endpoint['name']):
                response = self.client.get(endpoint['url'])
                self.assertEqual(
                    response.status_code, 200,
                    f"Error on endpoint: {endpoint['name']} ({endpoint['url']})"
                )
class LoginTest(TestCase):
    def setUp(self):
        self.username = 'TestTest'
        self.password = 'Finalniproject2024'
        self.user = User.objects.create_user(username=self.username, password=self.password)

    def test_login(self):
        response = self.client.post(reverse('login'), {
            'username': self.username,
            'password': self.password
        })

# class AuctionTest(TestCase):
#     def setUp(self):
#     self.profile = Profile.objects.get(user__username='TestTest')
#     Auction.objects.create(
#         name="Test Auction",
#         description="This is a test auction.",
#         seller=profile,
#         starting_price=100.00,
#         current_price=100.00,
#         end_time=now() + timedelta(days=7)