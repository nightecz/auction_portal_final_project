from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator
from django.db.models import (
    DO_NOTHING, CharField, DateField, DateTimeField, ForeignKey, IntegerField,
    Model, TextField, ImageField, OneToOneField, CASCADE, DecimalField, ManyToManyField
)


class Category(Model):
    name = CharField(max_length=128, unique=True)

    def __str__(self):
        return self.name


class Profile(Model):
    user = OneToOneField(User, on_delete=CASCADE, related_name='profile')
    phone = CharField(max_length=20)
    address = TextField()
    created_at = DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username


class Auction(Model):
    name = CharField(max_length=128)
    description = CharField(max_length=255)
    seller = ForeignKey(Profile, on_delete=CASCADE)
    starting_price = DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    current_price = DecimalField(max_digits=10, decimal_places=2, default=0)
    start_time = DateTimeField(auto_now_add=True)
    end_time = DateTimeField()
    categories = ManyToManyField('Category', related_name='auctions')

    def __str__(self):
        return self.name


class Watchlist(Model):
    user = OneToOneField(User, on_delete=CASCADE, related_name='watchlist')
    auctions = ManyToManyField('Auction', related_name='watchlists')

    def __str__(self):
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


class AuctionImage(Model):
    auction = ForeignKey(Auction, on_delete=CASCADE, related_name='images')
    image = ImageField(upload_to='auction_images/',
                       validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])])
    description = CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f'Image for {self.auction.name}'