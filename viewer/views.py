from django.contrib.auth.decorators import login_required
from django.utils import timezone
from decimal import Decimal

from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect, Http404
from django.contrib import messages
from django.contrib.auth import logout, login
from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect
from django.db.models import CharField, TextField, DateTimeField, ForeignKey
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import FormView, ListView, TemplateView, UpdateView, DeleteView, DetailView
from viewer.forms import SignUpForm, AuctionCreateForm, ProfileEditForm, BidForm
from django.urls import reverse_lazy, reverse
from viewer.models import Watchlist, Auction, User, Profile, Bid
from django.contrib.auth.forms import UserChangeForm

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
        # messages.success(self.request, "Přihlášení se podařilo")
        print("Error: wrong login")
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
        context['auction'] = Auction.objects.get(pk=auction_id)
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
            return HttpResponseBadRequest("No auction specified.")

        try:
            auction = Auction.objects.get(pk=auction_id)
        except Auction.DoesNotExist:
            return HttpResponseBadRequest("Auction does not exist.")

        if auction.seller == request.user:
            messages.error(request, "You cannot place a bid on your own auction.")
            return HttpResponseRedirect(reverse('auction_detail', kwargs={'id': auction_id}))

        form = BidForm(request.POST)

        if not form.is_valid():
            return HttpResponseBadRequest("Invalid bid value.")

        bid_amount = form.cleaned_data['bid_amount']

        if auction.end_time < timezone.now():
            return HttpResponseBadRequest("This auction is closed.")

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