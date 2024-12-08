from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import (
    DO_NOTHING, CharField, DateField, DateTimeField, ForeignKey, IntegerField,
    Model, TextField, ImageField
)

class Category(Model):
    name = CharField(max_length=128)

    def __str__(self):
        return self.name

class Auction(Model):
    pass

class Watchlist(Model):
  pass