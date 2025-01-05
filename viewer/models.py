from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator
from django.db.models import (
    DO_NOTHING, CharField, DateField, DateTimeField, ForeignKey, IntegerField,
    Model, TextField, ImageField, OneToOneField, CASCADE, DecimalField, ManyToManyField, BooleanField, SET_NULL
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
        if self.user:
            return self.user.username  # Zajišťujeme, že se používá uživatelský objekt
        return "No user associated"

    def calculate_average_rating(self):
        reviews = self.received_reviews.all()
        if reviews:
            return sum(review.rating for review in reviews) / len(reviews)
        return None


class Auction(Model):
    RUNNING = 'Running'
    CLOSED = 'Closed'
    SOLD = 'Sold'
    CANCELLED = 'Cancelled'
    STATUS_CHOICES = [
        (RUNNING, 'Running'),
        (CLOSED, 'Closed'),
        (SOLD, 'Sold'),
        (CANCELLED, 'Cancelled')
    ]

    name = CharField(max_length=128)
    description = CharField(max_length=255)
    seller = ForeignKey(User, on_delete=CASCADE)
    starting_price = DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    current_price = DecimalField(max_digits=10, decimal_places=2, default=0)
    start_time = DateTimeField(auto_now_add=True)
    end_time = DateTimeField()
    categories = ManyToManyField('Category', related_name='auctions')
    purchase = OneToOneField(
        'Purchase',
        on_delete=SET_NULL,
        null=True,
        blank=True,
        related_name='related_auction'
    )
    image1 = ImageField(upload_to='auctions/', blank=True, null=True, validators=[
        FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])
    ])
    image2 = ImageField(upload_to='auctions/', blank=True, null=True, validators=[
        FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])
    ])
    image3 = ImageField(upload_to='auctions/', blank=True, null=True, validators=[
        FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])
    ])
    status = CharField(max_length=10,
                       choices=STATUS_CHOICES,
                       default=RUNNING,
                    )
    buy_now_price = DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)



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


class Bid(Model):
    auction = ForeignKey(Auction, on_delete=CASCADE, related_name='bids')
    bidder = ForeignKey(User, on_delete=CASCADE, related_name='bids')
    amount = DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    created_at = DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.bidder.username} bid {self.amount} on {self.auction.name}"

    class Meta:
        get_latest_by = 'created_at'


class Purchase(Model):
    auction = ForeignKey(Auction, on_delete=CASCADE, related_name='purchases')
    buyer = ForeignKey('Profile', on_delete=CASCADE, related_name='purchases_as_buyer')
    seller = ForeignKey('Profile', on_delete=CASCADE, related_name='purchases_as_seller')
    amount = DecimalField(max_digits=10, decimal_places=2, default=0.00)
    purchase_date = DateTimeField(auto_now_add=True)
    seller_confirmation = BooleanField(default=False)
    winning_price = DecimalField(max_digits=10, decimal_places=2, default=0.00)
    buyer_confirmation = BooleanField(default=False)

    def __str__(self):
        return f" Winner of {self.auction.name} is {self.buyer.user.username} for ${self.winning_price}"

class Review(Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]  # 1-5 stars

    reviewer = ForeignKey('Profile', on_delete=CASCADE, related_name='written_reviews')
    reviewee = ForeignKey('Profile', on_delete=CASCADE, related_name='received_reviews')
    purchase = ForeignKey('Purchase', on_delete=CASCADE, related_name='reviews')
    rating = IntegerField(choices=RATING_CHOICES)
    text = TextField(blank=True, null=True)
    created = DateTimeField(auto_now_add=True)

    def __str__(self):
      return f" Review from {self.reviewer} for {self.reviewee} is {self.rating}/5"