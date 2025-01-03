from django.contrib import admin
from .models import Category, Auction, Profile, Watchlist, Bid, Purchase, Review

admin.site.register(Auction)
admin.site.register(Category)
admin.site.register(Profile)
admin.site.register(Watchlist)
admin.site.register(Bid)
admin.site.register(Purchase)
admin.site.register(Review)