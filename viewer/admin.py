from django.contrib import admin
from .models import Category, Auction, AuctionImage

admin.site.register(Auction)
admin.site.register(Category)
# admin.site.register(Image)
# admin.site.register(Review)
admin.site.register(AuctionImage)