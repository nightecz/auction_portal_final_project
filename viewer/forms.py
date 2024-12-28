import re
from django.contrib.auth.forms import UserChangeForm
from django.core.exceptions import ValidationError
from viewer.models import Profile, Bid
from django.forms import (
    CharField, DateField, Form, IntegerField, ModelChoiceField, Textarea, TextInput, EmailInput, PasswordInput,
    ModelForm, DateInput, NumberInput, CheckboxSelectMultiple, DateTimeInput, DecimalField, ChoiceField
)
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from viewer.models import Auction, Category, Watchlist
from django.urls import reverse_lazy
from django.shortcuts import redirect

class SignUpForm(UserCreationForm):
    first_name = CharField(max_length=20, required=True, label='First name')
    last_name = CharField(max_length=20, required=True, label='Last name')
    phone = CharField(max_length=20, required=True, label='Phone')
    street = CharField(max_length=20, required=True, label='Street')
    house_number = CharField(max_length=20, required=True, label='Address House number')
    city = CharField(max_length=20, required=True, label='City')
    zip_code = CharField(max_length=20, required=True, label='ZIP code')
    country = CharField(max_length=20, required=True, label='Country')
    prefer_communication = ChoiceField(
        choices=Profile.COMMUNICATION_CHOICES,
        required=True,
        label="Prefered communication via"
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'first_name', 'last_name', 'phone', 'street', 'house_number', 'city', 'zip_code', 'country', 'prefer_communication']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            self.fields[field_name].widget.attrs['class'] = 'form-control'

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()

        profile = Profile.objects.create(
            user=user,
            phone=self.cleaned_data['phone'],
            street=self.cleaned_data['street'],
            house_number=self.cleaned_data['house_number'],
            city=self.cleaned_data['city'],
            zip_code=self.cleaned_data['zip_code'],
            country=self.cleaned_data['country'],
            prefer_communication=self.cleaned_data['prefer_communication']
        )

        return user

class ProfileEditForm(ModelForm):
    class Meta:
        model = Profile
        fields = ['avatar']

class AuctionCreateForm(ModelForm):
    class Meta:
        model = Auction
        fields = ['name', 'description', 'starting_price', 'end_time', 'categories', 'image']
        widgets = {
            'description': Textarea(),
            'categories': CheckboxSelectMultiple(),
            'end_time': DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            self.fields[field_name].widget.attrs['class'] = 'form-control'
        self.fields['categories'].widget.attrs.pop('class', None)



    def save(self, commit=True):
        auction = super().save(commit=False)  # Nejprve uložíme aukci bez okamžitého commitu do DB
        if not auction.current_price:
            auction.current_price = auction.starting_price  # Pokud není current_price, nastavíme ho na starting_price
        if commit:
            auction.save()  # Uložíme aukci do databáze
            self.save_m2m()
        return auction

class AuctionUpdateForm(ModelForm):
    class Meta:
        model = Auction
        fields = ['description', 'categories', 'image'] #permitted field
        widgets = {
            'description': Textarea(),
            'categories': CheckboxSelectMultiple(),
        }

class BidForm(ModelForm):
    bid_amount = DecimalField(label='Place Your Bid', widget=NumberInput(attrs={
        'class': 'form-control',
        'step': '0.01',
        'min': '0'
    }))

    class Meta:
        model = Bid
        fields = ['bid_amount']


class WatchlistForm(ModelForm):
    class Meta:
        model = Watchlist
        fields = ['auction']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['auction'].widget.attrs['class'] = 'form-control'