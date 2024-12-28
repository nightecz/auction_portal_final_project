from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator
from django.db.models import (
    DO_NOTHING, CharField, DateField, DateTimeField, ForeignKey, IntegerField,
    Model, TextField, ImageField, OneToOneField, CASCADE, DecimalField, ManyToManyField, BooleanField
)


class Category(Model):
    name = CharField(max_length=128, unique=True)
    parent = ForeignKey(
        'self', null=True, blank=True, related_name='subcategories', on_delete=CASCADE
    )
    def __str__(self):
        return self.name

class Profile(Model):
    COMMUNICATION_CHOICES = [
        ('mail', 'Post'),
        ('email', 'Email'),
    ]

    user = OneToOneField(User, on_delete=CASCADE, related_name='profile', unique=True)
    phone = CharField(max_length=20, blank=True, null=True)
    street = CharField(max_length=20, blank=True, null=True)
    house_number = CharField(max_length=20, blank=True, null=True)
    city = CharField(max_length=20, blank=True, null=True)
    zip_code = CharField(max_length=20, blank=True, null=True)
    country = CharField(max_length=20, blank=True, null=True)
    avatar = ImageField(upload_to='avatars/', blank=True, null=True, validators=[
        FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])
    ])
    created_at = DateTimeField(auto_now_add=True)
    is_premium = BooleanField(default=False)  # Premium user
    prefer_communication = CharField(
        max_length=10,
        choices=COMMUNICATION_CHOICES,
        default='email',
    )
    first_name = CharField(max_length=20, blank=True, null=True)
    last_name = CharField(max_length=20, blank=True, null=True)
    def __str__(self):
        return self.user.username


class Auction(Model):
    name = CharField(max_length=128)
    description = CharField(max_length=255)
    seller = ForeignKey(User, on_delete=CASCADE)
    starting_price = DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    current_price = DecimalField(max_digits=10, decimal_places=2, default=0)
    start_time = DateTimeField(auto_now_add=True)
    end_time = DateTimeField()
    categories = ManyToManyField('Category', related_name='auctions')
    image = ImageField(upload_to='auctions/', blank=True, null=True, validators=[
        FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])
    ])

    class Meta:
        permissions = [
            ("auction_update", "Can edit auction"),
        ]
    def save(self, *args, **kwargs):
        if self.pk is None:
            self.current_price = self.starting_price
        super().save(*args, **kwargs)

class Watchlist(Model):
    user = ForeignKey(User, on_delete=CASCADE, related_name='watchlist')
    auction = ForeignKey(Auction, on_delete=CASCADE, null=True)

    class Meta:
        unique_together = ('user', 'auction')
    def __str__(self):
        return self.user.username
        return self.user.username

class Bid(Model):
    auction = ForeignKey(Auction, on_delete=CASCADE, related_name='bids')
    bidder = ForeignKey(User, on_delete=CASCADE, related_name='bids')
    amount = DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    created_at = DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.bidder.username} bid {self.amount} on {self.auction.name}"


class Purchase(Model):
    auction = ForeignKey(Auction, on_delete=CASCADE, related_name='purchase')
    buyer = ForeignKey(Profile, on_delete=DO_NOTHING)
    winning_price = DecimalField(max_digits=10, decimal_places=2)
    purchase_date = DateTimeField(auto_now_add=True)

    def __str__(self):
        return f" Winner of {self.auction.name} is {self.buyer.username} for {self.winning_price}"