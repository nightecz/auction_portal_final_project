from django.contrib import admin
from .models import Category, Auction

admin.site.register(Auction)
admin.site.register(Category)
# admin.site.register(Image)
# admin.site.register(Review)