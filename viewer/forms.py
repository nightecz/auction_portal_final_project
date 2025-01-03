import re
from django.contrib.auth.forms import UserChangeForm
from django.core.exceptions import ValidationError
from django.forms.widgets import HiddenInput

from viewer.models import Profile, Bid, Purchase
from django.forms import (
    CharField, DateField, Form, IntegerField, ModelChoiceField, Textarea, TextInput, EmailInput, PasswordInput,
    ModelForm, DateInput, NumberInput, CheckboxSelectMultiple, DateTimeInput, DecimalField, ChoiceField, ModelMultipleChoiceField
)
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from viewer.models import Auction, Category, Watchlist, Review
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
    subcategories = ModelMultipleChoiceField(
        queryset=Category.objects.filter(parent__isnull=False),
        required=False,
        widget=CheckboxSelectMultiple(),
        label="Subcategories (optional)"
    )
    class Meta:
        model = Auction
        fields = ['name', 'description', 'starting_price', 'end_time', 'categories', 'image1', 'image2', 'image3']
        widgets = {
            'description': Textarea(),
            'categories': CheckboxSelectMultiple(attrs={'class': 'form-control'}),
            'end_time': DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        #only main_category is visible
        self.fields['categories'].queryset = Category.objects.filter(parent__isnull=True)
        #only sub_categories are visible
        self.fields['subcategories'].queryset = Category.objects.filter(parent__isnull=False)

        for field_name in self.fields:
            self.fields[field_name].widget.attrs['class'] = 'form-control'
        self.fields['categories'].widget.attrs.pop('class', None)
        self.fields['subcategories'].widget.attrs.pop('class', None)

    def clean_categories(self):
        categories = self.cleaned_data.get('categories')
        if categories.count() > 1:
            raise ValidationError("You can select only one main category.")
        return categories

    def clean_subcategories(self):
        subcategories = self.cleaned_data.get('subcategories')
        if subcategories and subcategories.count() > 2:
            raise ValidationError("You can select up to two subcategories.")
        return subcategories

    def save(self, commit=True):
        auction = super().save(commit=False)  # Nejprve uložíme aukci bez okamžitého commitu do DB
        if not auction.current_price:
            auction.current_price = auction.starting_price  # Pokud není current_price, nastavíme ho na starting_price
        if commit:
            auction.save()  # Uložíme aukci do databáze
            self.save_m2m()
        return auction

class AuctionUpdateForm(ModelForm):
    subcategories = ModelMultipleChoiceField(
        queryset=Category.objects.filter(parent__isnull=False),
        required=False,
        widget=CheckboxSelectMultiple(),
        label="Subcategories (optional)"
    )
    class Meta:
        model = Auction
        fields = ['description', 'categories', 'image1', 'image2', 'image3'] #permitted field
        widgets = {
            'description': Textarea(),
            'categories': CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # only main_category is visible
        self.fields['categories'].queryset = Category.objects.filter(parent__isnull=True)
        # only sub_categories are visible
        self.fields['subcategories'].queryset = Category.objects.filter(parent__isnull=False)

        # add classes to form fields
        for field_name in self.fields:
            self.fields[field_name].widget.attrs['class'] = 'form-control'
        self.fields['categories'].widget.attrs.pop('class', None)
        self.fields['subcategories'].widget.attrs.pop('class', None)

        # Pre-fill 'subcategories' with the current subcategories of the auction
        if self.instance.pk:
            self.fields['subcategories'].initial = self.instance.categories.filter(parent__isnull=False)

    def clean_categories(self):
        categories = self.cleaned_data.get('categories')
        if categories.count() > 1:
            raise ValidationError("You can select only one main category.")
        return categories

    def clean_subcategories(self):
        subcategories = self.cleaned_data.get('subcategories')
        if subcategories and subcategories.count() > 2:
            raise ValidationError("You can select up to two subcategories.")
        return subcategories

    def save(self, commit=True):
        # Get the instance of Auction object being updated
        auction = super().save(commit=False)

        # Ensure the main category is added to categories
        main_category = self.cleaned_data.get('categories')
        if main_category:
            auction.categories.set(main_category)

        # Add subcategories
        subcategories = self.cleaned_data.get('subcategories')
        if subcategories:
            auction.categories.add(*subcategories)

        if commit:
            auction.save()
        return auction

class BidForm(ModelForm):
    bid_amount = DecimalField(label='Place Your Bid', widget=NumberInput(attrs={
        'class': 'form-control',
        'step': '0.1',
        'min': '0,1'
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


class PurchaseForm(ModelForm):
    class Meta:
        model = Purchase
        fields = ['winning_price', 'buyer']

class ReviewForm(ModelForm):
    class Meta:
        model = Review
        fields = ["rating", "text"]

        widgets = {
            'rating': NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5}),
            'text': Textarea(attrs={'class': 'form-control'})
        }
    def __init__(self, *args, **kwargs): # text is not required
        super().__init__(*args, **kwargs)
        self.fields['text'].required = False