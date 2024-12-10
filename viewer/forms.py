import re

from django.core.exceptions import ValidationError
from django.forms import (
    CharField, DateField, Form, IntegerField, ModelChoiceField, Textarea, TextInput, EmailInput, PasswordInput,
    ModelForm, DateInput, NumberInput, CheckboxSelectMultiple
)

# from viewer.models import Auction
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from viewer.models import Auction, Category


class SignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            self.fields[field_name].widget.attrs['class'] = 'form-control'


class AuctionCreateForm(ModelForm):
    class Meta:
        model = Auction
        fields = ['name', 'description', 'starting_price', 'end_time', 'categories']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            self.fields[field_name].widget.attrs['class'] = 'form-control'

    def save(self, commit=True):
        auction = super().save(commit=False)  # Nejprve uložíme aukci bez okamžitého commitu do DB
        if not auction.current_price:
            auction.current_price = auction.starting_price  # Pokud není current_price, nastavíme ho na starting_price
        if commit:
            auction.save()  # Uložíme aukci do databáze
        return auction
