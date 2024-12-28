import os
from datetime import timedelta

import django
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils.timezone import now

from viewer.models import Profile, Auction

os.environ['DJANGO_SETTINGS_MODULE'] = 'final_project.settings'
django.setup()

#test for not logged user
class UrlsTests(TestCase):
    def test_urls(self):
        endpoints = [
            {'url': reverse('index'), 'name': 'index'},
            {'url': reverse('login'), 'name': 'login'},
            {'url': reverse('register'), 'name': 'register'},
            {'url': reverse('auctions'), 'name': 'auctions'},
        ]

        for endpoint in endpoints:
            with self.subTest(endpoint=endpoint['name']):
                response = self.client.get(endpoint['url'])
                self.assertEqual(
                    response.status_code, 200,
                    f"Error on endpoint: {endpoint['name']} ({endpoint['url']})"
                )
#Tests for login User and his functionalities
class LoginUserTest(TestCase):
    def setUp(self):
        self.username = 'TestTest'
        self.password = 'Finalniproject2024'
        self.user = User.objects.create_user(username=self.username, password=self.password)

    def test_login(self):
        response = self.client.post(reverse('login'), {
            'username': self.username,
            'password': self.password
        })
    def test_profile(self):
        endpoint = {'url': reverse('profile'), 'name': 'profile'}

    def test_auction_create(self):
        endpoint = {'url': reverse('auction_create'), 'name': 'auction_create'},

class AuctionCreateTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='TestTest', password='password123')
        self.profile = Profile.objects.create(user=self.user)

    def test_auction_creation(self):
        auction = Auction.objects.create(
            name="Test Auction",
            description="This is a test auction.",
            seller=self.user,
            starting_price=100.00,
            current_price=100.00,
            end_time=now() + timedelta(days=7)
        )

        self.assertEqual(auction.name, "Test Auction")
        self.assertEqual(auction.seller, self.user)
        self.assertEqual(auction.starting_price, 100.00)
        self.assertEqual(auction.current_price, 100.00)

class LogoutUserTest(TestCase):
    pass