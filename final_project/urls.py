from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views
from django.urls import path
from viewer.views import (index, CustomLoginView, ProfileView, RegisterView, AuctionView, WatchlistView,
                          AuctionCreateView, ProfileEditView, AuctionDetailView, AuctionSellingView, PlaceBidView,
                          AddToWatchlistView, WatchlistDeleteView, AuctionSearchView, AuctionUpdateView, ContactInfoView,
                          SellerConfirmView, BuyerConfirmView, AuctionCancelView, AuctionBiddingView)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name='index'),

    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('register/', RegisterView.as_view(), name='register'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/edit/', ProfileEditView.as_view(), name='profile_edit'),

    path('auctions/', AuctionView.as_view(), name='auctions'),
    path('auctions/my_auctions/', AuctionSellingView.as_view(), name='my_auctions'),
    path('auctions/bidding', AuctionBiddingView.as_view(), name='bidding'),

    path('auction_create/', AuctionCreateView.as_view(), name='auction_create'),
    path('auction/detail/<int:id>/', AuctionDetailView.as_view(), name='auction_detail'),
    path('auction/bid/', PlaceBidView.as_view(), name='place_bid'),
    path('auction/advanced_search', AuctionSearchView.as_view(), name='advanced_search'),
    path('auction/update/<pk>', AuctionUpdateView.as_view(), name='auction_update'),
    path('auction/cancel/<pk>/', AuctionCancelView.as_view(), name='auction_cancel'),

    path('auction/<int:purchase_id>/buyer-confirmation/', BuyerConfirmView.as_view(), name='buyer_confirmation'),
    path('auction/<int:purchase_id>/seller-confirmation/', SellerConfirmView.as_view(), name='seller_confirmation'),
    path('contact-info/<int:purchase_id>/', ContactInfoView.as_view(), name='contact_info'),

    path('watchlist/', WatchlistView.as_view(), name='watchlist'),
    path('add-to-watchlist/<int:auction_id>/', AddToWatchlistView.as_view(), name='add_to_watchlist'),
    path('remove_from_watchlist/<int:pk>/', WatchlistDeleteView.as_view(), name='remove_from_watchlist'),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
