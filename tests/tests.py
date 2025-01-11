import os
from datetime import timedelta, datetime

import django
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils.timezone import now

from viewer.models import Profile, Auction, Category
from viewer.forms import SignUpForm, AuctionCreateForm

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


class TestSignUpFormValidator(TestCase):

    def test_valid_phone_number(self):
        form_data = self._get_valid_data(phone='+420200000000')
        form = SignUpForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_phone_number_missing_plus(self):
        form_data = self._get_valid_data(phone='420200000000')
        form = SignUpForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('phone', form.errors)

    def test_invalid_phone_number_too_few_digits(self):
        form_data = self._get_valid_data(phone='+42020000000')  # 11 digits
        form = SignUpForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('phone', form.errors)

    def test_invalid_first_name_special_characters(self):
        form_data = self._get_valid_data(first_name='Tomáš!')
        form = SignUpForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('first_name', form.errors)

    def test_invalid_last_name_digits(self):
        form_data = self._get_valid_data(last_name='Nov8k')
        form = SignUpForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('last_name', form.errors)

    def test_invalid_street_special_characters(self):
        form_data = self._get_valid_data(street='Na_hrázi')
        form = SignUpForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('street', form.errors)

    def test_invalid_city_special_characters(self):
        form_data = self._get_valid_data(city='Horní-dolní')
        form = SignUpForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('city', form.errors)

    def test_invalid_zip_code_special_characters(self):
        form_data = self._get_valid_data(zip_code='#55555')
        form = SignUpForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('zip_code', form.errors)

    def test_invalid_zip_code_too_few_digits(self):
        form_data = self._get_valid_data(zip_code='4444')  # Too few digits
        form = SignUpForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('zip_code', form.errors)

    def test_invalid_country_special_characters(self):
        form_data = self._get_valid_data(country='Česká-republika')
        form = SignUpForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('country', form.errors)

    def test_valid_email(self):
        form_data = self._get_valid_data(email='test@example.com')
        form = SignUpForm(data=form_data)
        if not form.is_valid():
            print(form.errors)
        self.assertTrue(form.is_valid())

    def test_invalid_email(self):
        form_data = self._get_valid_data(email='invalid-email')
        form = SignUpForm(data=form_data)

        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)


    # Helper method for valid data
    def _get_valid_data(self, phone='+420200000000', first_name='Tomáš', last_name='Novák',
                        street='Na hrázi', city='Praha', zip_code='11000', country='Česká republika', email='test@example.com'):
        return {
            'username': 'testuser',
            'email': email,
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
            'first_name': first_name,
            'last_name': last_name,
            'phone': phone,
            'street': street,
            'house_number': '123',
            'city': city,
            'zip_code': zip_code,
            'country': country,
            'prefer_communication': 'email',
        }

class TestAuctionCreateForm(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Electronics", parent=None)

    def test_valid_starting_price(self):
        form_data = self._get_valid_data(starting_price=100.01)
        form = AuctionCreateForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_starting_price(self):
        form_data = self._get_valid_data(starting_price=-100.01)
        form = AuctionCreateForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('starting_price', form.errors)

    def test_valid_buy_now_price(self):
        form_data = self._get_valid_data(buy_now_price=100.01)
        form = AuctionCreateForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_buy_now_price(self):
        form_data = self._get_valid_data(buy_now_price=-100.01)
        form = AuctionCreateForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('buy_now_price', form.errors)

    def _get_valid_data(self, starting_price=100.00, buy_now_price=100.00):
        return {
            'name': 'Produkt',
            'description': 'realy great Produkt',
            'starting_price': starting_price,
            'buy_now_price': buy_now_price,
            'end_time': '2025-01-15T14:30',
            'categories': [1],
        }
