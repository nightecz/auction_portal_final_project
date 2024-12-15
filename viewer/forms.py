import re
from django.contrib.auth.forms import UserChangeForm
from django.core.exceptions import ValidationError
from viewer.models import Profile
from django.forms import (
    CharField, DateField, Form, IntegerField, ModelChoiceField, Textarea, TextInput, EmailInput, PasswordInput,
    ModelForm, DateInput, NumberInput, CheckboxSelectMultiple, DateTimeInput
)
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from viewer.models import Auction, Category
from django.urls import reverse_lazy
from django.shortcuts import redirect

class SignUpForm(UserCreationForm):
    street = CharField(max_length=20, required=True, label='Street')
    house_number = CharField(max_length=20, required=True, label='Address House number')
    city = CharField(max_length=20, required=True, label='City')
    zip_code = CharField(max_length=20, required=True, label='ZIP code')
    country = CharField(max_length=20, required=True, label='Country')

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'street', 'house_number', 'city', 'zip_code', 'country']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            self.fields[field_name].widget.attrs['class'] = 'form-control'

class ProfileEditForm(ModelForm):
    class Meta:
        model = Profile
        fields = ['avatar']

class AuctionCreateForm(ModelForm):
    class Meta:
        model = Auction
        fields = ['name', 'description', 'starting_price', 'end_time', 'categories', 'image']
        widgets = {
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
