import unicodedata
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator, EmailValidator

from viewer.models import Profile, Bid, Purchase
from django.forms import (
    CharField, Textarea,
    ModelForm, NumberInput, CheckboxSelectMultiple, DateTimeInput, DecimalField, ChoiceField, ModelMultipleChoiceField
)
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from viewer.models import Auction, Category, Watchlist, Review


class SignUpForm(UserCreationForm):
    first_name = CharField(max_length=20, required=True, label='First name')
    last_name = CharField(max_length=20, required=True, label='Last name')
    phone = CharField(max_length=20,
                      required=True,
                      label='Phone (in standard format with area code eg.: +420 999 999 999)',
                      validators=[
                            RegexValidator(
                                regex=r'^\+\d{12}$', #regular expresion - have to contain + and 12 digits
                                message="Phone number have to be in standard phone format with area code."
                            )
                        ]
                    )
    street = CharField(max_length=20, required=True, label='Street')
    house_number = CharField(max_length=20, required=True, label='House number')
    city = CharField(max_length=20, required=True, label='City')
    zip_code = CharField(max_length=20, required=True, label='ZIP code',
                         validators=[
                            RegexValidator(
                                regex=r'^\d{5}$', #regular expresion - have to consist of 5 digits.
                                message="ZIP code must consist of exactly 5 digits."
                            )
                        ]
                    )
    country = CharField(max_length=20, required=True, label='Country')
    prefer_communication = ChoiceField(
        choices=Profile.COMMUNICATION_CHOICES,
        required=True,
        label="Prefered communication via"
    )
    email = CharField(
        required=True,
        label='Email',
        validators=[EmailValidator(message="Enter a valid email address.")] # Django core default validator
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'first_name', 'last_name', 'phone', 'street', 'house_number', 'city', 'zip_code', 'country', 'prefer_communication']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            self.fields[field_name].widget.attrs['class'] = 'form-control'

    def normalize_name(self, name):
        """Normalize name to ensure proper capitalization and handle diacritics."""
        # Capitalize the first character and keep the rest unchanged
        return name[:1].upper() + name[1:].lower()

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if not all(unicodedata.category(char).startswith('L') for char in first_name):
            raise ValidationError("First name must contain only letters.")
        return self.normalize_name(first_name)

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if not all(unicodedata.category(char).startswith('L') for char in last_name):
            raise ValidationError("Last name must contain only letters.")
        return self.normalize_name(last_name)

    def clean_street(self):
        street = self.cleaned_data.get('street')
        if not all(unicodedata.category(char).startswith('L') or char.isspace() for char in street):
            raise ValidationError("Street must contain only letters and spaces.")
        return self.normalize_name(street)

    def clean_city(self):
        city = self.cleaned_data.get('city')
        if not all(unicodedata.category(char).startswith('L') or char.isspace() for char in city):
            raise ValidationError("City must contain only letters and spaces.")
        return self.normalize_name(city)

    def clean_country(self):
        country = self.cleaned_data.get('country')
        if not all(unicodedata.category(char).startswith('L') or char.isspace() for char in country):
            raise ValidationError("Country must contain only letters and spaces.")
        return self.normalize_name(country)

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
        fields = ['name', 'description', 'starting_price','buy_now_price', 'end_time', 'categories', 'image1', 'image2', 'image3']
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

    def clean_starting_price(self):
        starting_price = self.cleaned_data.get('starting_price')
        if starting_price < 0.01:
            raise ValidationError("Starting price must be greater than zero.")
        return starting_price

    def clean_buy_now_price(self):
        buy_now_price = self.cleaned_data.get('buy_now_price')
        if buy_now_price < 0.01:
            raise ValidationError("Buy now price must be greater than zero.")
        return buy_now_price

    def save(self, commit=True):
        auction = super().save(commit=False)
        if not auction.current_price:
            auction.current_price = auction.starting_price
        if commit:
            auction.save()
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