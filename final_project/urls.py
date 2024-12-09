from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views
from django.urls import path
# from viewer.models import Auction
from viewer.views import (index, CustomLoginView, ProfileView, RegisterView, AuctionView, WatchlistView)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name='index'),

    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('register/', RegisterView.as_view(), name='register'),
    path('profile/', ProfileView.as_view(), name='profile'),

    path('auctions/', AuctionView.as_view(), name='auctions'),

    path('watchlist/', WatchlistView.as_view(), name='watchlist'),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)