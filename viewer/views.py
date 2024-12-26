from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect, Http404
from django.contrib import messages
from django.contrib.auth import logout, login
from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import FormView, ListView, TemplateView
from viewer.forms import SignUpForm, AuctionCreateForm, ProfileEditForm, BidForm, PurchaseForm
from django.urls import reverse_lazy, reverse
from viewer.models import Watchlist, Auction, User, Profile, Bid, Purchase


def index(request):
    value = request.GET.get('value', '')
    return render(request, template_name='index.html', context={'value': value})


class RegisterView(FormView):
    template_name = 'registration/register.html'
    form_class = SignUpForm
    success_url = reverse_lazy('profile')

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect(self.success_url)

    def form_invalid(self, form):
        messages.error(self.request, form.errors)
        return super().form_invalid(form)


class CustomLoginView(LoginView):
    template_name = 'registration/login.html'

    def form_invalid(self, form):
        messages.error(self.request, "Wrong username or password")
        return super().form_invalid(form)

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('/')
        return super().dispatch(request, *args, **kwargs)


class ProfileView(TemplateView):
    template_name = 'profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.request.user.profile
        return context


class ProfileEditView(View):
    template_name = 'profile_edit.html'
    form_class = ProfileEditForm
    success_url = reverse_lazy('profile')

    def get(self, request, *args, **kwargs):
        form = self.form_class(instance=request.user.profile)
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            return redirect(self.success_url)
        return render(request, self.template_name, {'form': form})


class AuctionView(ListView):
    template_name = 'auctions.html'
    model = Auction


class AuctionCreateView(FormView):
    template_name = 'auction_create.html'
    form_class = AuctionCreateForm
    success_url = reverse_lazy('auctions')

    def form_valid(self, form):
        cleaned_data = form.cleaned_data
        auction = Auction.objects.create(
            name=cleaned_data['name'],
            description=cleaned_data['description'],
            starting_price=cleaned_data['starting_price'],
            end_time=cleaned_data['end_time'],
            seller=self.request.user,
            image=cleaned_data.get('image')
        )
        categories = form.cleaned_data['categories']
        auction.categories.set(categories)
        return super().form_valid(form)


class AuctionDetailView(TemplateView):
    template_name = 'auction_detail.html'
    context_object_name = 'auction'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        auction_id = self.kwargs.get('id')
        auction = Auction.objects.get(pk=auction_id)

        print(f"Auction status: {auction.status}")

        context['auction'] = auction

        # Načtení Purchase z databáze, pokud existuje
        try:
            purchase = Purchase.objects.get(auction=auction)
            print(f"Purchase found: {purchase}")
        except Purchase.DoesNotExist:
            purchase = None
            print(f"No purchase record found for auction {auction.id}")


        def close_auction_and_create_purchase(auction):
            print(f"Closing auction: {auction.id}")
            if auction.status == Auction.CLOSED and not auction.purchases.exists():
                if auction.bids.exists():
                    highest_bid = auction.bids.latest('created_at')
                    print(f"Highest bid: {highest_bid.amount} by {highest_bid.bidder.username}")
                    purchase = Purchase.objects.create(
                        auction=auction,
                        buyer=highest_bid.bidder.profile,
                        seller=auction.seller.profile,
                        winning_price=highest_bid.amount
                    )
                    purchase.save()  # Explicitně uložit Purchase
                    print(f"Purchase created: {purchase}")
                    return purchase
            return None

        if auction.end_time < timezone.now() and auction.status != Auction.CLOSED:
            auction.status = Auction.CLOSED
            auction.save()
            print(f"Auction {auction.id} status updated to CLOSED")

            purchase = close_auction_and_create_purchase(auction)

        context['purchase'] = purchase
        context['current_time'] = timezone.now()

        print(f"Context purchase: {context['purchase']}")
        return context




class AuctionSellingView(ListView):
    template_name = 'my_auctions.html'
    model = Auction

    def get_queryset(self):
        return Auction.objects.filter(seller=self.request.user)

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)


class PlaceBidView(FormView):
    template_name = 'auction_detail.html'
    form_class = BidForm
    success_url = reverse_lazy('auction_detail')


    def post(self, request, *args, **kwargs):
        auction_id = request.GET.get('auction')
        if not auction_id:
            return HttpResponseBadRequest("No auction specified")

        try:
            auction = Auction.objects.get(pk=auction_id)
        except Auction.DoesNotExist:
            return HttpResponseBadRequest("Auction does not exist")

        if auction.seller == request.user:
            messages.error(request, "You cannot place a bid on your own auction.")
            return HttpResponseRedirect(reverse('auction_detail', kwargs={'id': auction_id}))

        form = BidForm(request.POST)

        if not form.is_valid():
            messages.error(request, "Invalid bid value.")
            return HttpResponseRedirect(reverse('auction_detail', kwargs={'id': auction_id}))

        bid_amount = form.cleaned_data['bid_amount']

        if auction.end_time < timezone.now():
            messages.error(request, "This auction is closed.")
            return HttpResponseRedirect(reverse('auction_detail', kwargs={'id': auction_id}))

        if bid_amount <= auction.current_price:
            messages.error(request, "Bid must be higher than current price.")
            return redirect(reverse('auction_detail', kwargs={'id': auction_id}))

        auction.current_price = bid_amount
        auction.save()

        auction.bids.create(
            bidder=request.user,
            amount=bid_amount
        )
        messages.success(request, "Your bid was placed.")
        return HttpResponseRedirect(reverse('auction_detail', kwargs={'id': auction_id}))


@method_decorator(login_required, name='dispatch')
class WatchlistView(ListView):
    template_name = "watchlist/watchlist.html"
    model = Watchlist

    def get_queryset(self):
        return Watchlist.objects.filter(user=self.request.user)


@login_required
def watchlist_add(request):
    auction_id = request.GET.get('auction')
    if not auction_id:
        return HttpResponseBadRequest("Auction ID is required.")

    try:
        auction = Auction.objects.get(pk=auction_id)
    except Auction.DoesNotExist:
        return HttpResponseBadRequest("Auction does not exist.")

    watchlist, created = Watchlist.objects.get_or_create(user=request.user)
    if watchlist.auctions.filter(pk=auction.pk).exists():
        messages.info(request, "Auction is already in your watchlist.")
    else:
        watchlist.auctions.add(auction)
        messages.success(request, "Auction added to your watchlist.")

    return redirect('watchlist')




class SellerConfirmView(View):
    def get(self, request, purchase_id):
        try:
            purchase = Purchase.objects.get(id=purchase_id)

            # Ensure the current user is the buyer
            if purchase.seller != request.user.profile:
                raise Http404("Not authorized to confirm the purchase")

            # Confirm purchase
            purchase.seller_confirmation = True
            purchase.save()

            return redirect('auction_detail', id=purchase.auction.id)

        except Purchase.DoesNotExist:
            raise Http404("Purchase does not exist")


class BuyerConfirmView(View):
    def get(self, request, purchase_id):
        try:
            purchase = Purchase.objects.get(id=purchase_id)

            # Ensure the current user is the buyer
            if purchase.buyer != request.user.profile:
                raise Http404("Not authorized to confirm the purchase")

            # Confirm purchase
            purchase.buyer_confirmation = True
            purchase.save()

            return redirect('auction_detail', id=purchase.auction.id)

        except Purchase.DoesNotExist:
            raise Http404("Purchase does not exist")