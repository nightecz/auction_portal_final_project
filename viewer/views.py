from django.contrib.auth.decorators import login_required
from django.utils import timezone
from decimal import Decimal

from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect, Http404
from django.contrib import messages
from django.contrib.auth import logout, login
from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import CharField, TextField, DateTimeField, ForeignKey, Q
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import FormView, ListView, TemplateView, UpdateView, DeleteView, DetailView
from viewer.forms import SignUpForm, AuctionCreateForm, ProfileEditForm, BidForm, WatchlistForm
from django.urls import reverse_lazy, reverse
from viewer.models import Watchlist, Auction, User, Profile, Bid, Category
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

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('q', '').strip()
        category_id = self.request.GET.get('category')

        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(categories__name__icontains=search_query)
            ).distinct()

        if category_id:
            queryset = queryset.filter(categories__id=category_id)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        if self.request.user.is_authenticated:
            user_watchlist = Watchlist.objects.filter(user=self.request.user)
            auction_ids_in_watchlist = user_watchlist.values_list('auction_id', flat=True)
            context['auction_ids_in_watchlist'] = auction_ids_in_watchlist
        return context

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

class AuctionSearchView(ListView):
    template_name = 'advanced_search.html'
    model = Auction
    context_object_name = 'auctions'
    paginate_by = 10  # numbers of auction on page

    def get_queryset(self):
        query = self.request.GET.get('q', '')
        auctions = Auction.objects.all()

        # Filtering by user task (keyword)
        if query:
            auctions = auctions.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(categories__name__icontains=query) |
                Q(seller__username__icontains=query)
            ).distinct()

        # Filtering by category
        category = self.request.GET.get('category')
        if category:
            auctions = auctions.filter(categories__id=category)

        # Premium auctions priority
        # auctions = auctions.order_by('-seller__profile__is_premium', '-created_at')

        # Filtering by city and end_time
        city = self.request.GET.get('city')
        if city:
            auctions = auctions.filter(seller__profile__city__icontains=city)

        sort_by = self.request.GET.get('sort_by')
        if sort_by == 'end_time':
            auctions = auctions.order_by('end_time')
        elif sort_by == 'start-time':
            auctions = auctions.order_by('-start-time')

        return auctions

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()  # Poskytne seznam kategorií pro filtr
        return context

class AuctionDetailView(TemplateView):
    template_name = 'auction_detail.html'
    context_object_name = 'auction'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        auction_id = self.kwargs.get('id')
        context['auction'] = Auction.objects.get(pk=auction_id)
        user_watchlist = Watchlist.objects.filter(user=self.request.user)
        auction_ids_in_watchlist = user_watchlist.values_list('auction_id', flat=True)
        context['auction_ids_in_watchlist'] = auction_ids_in_watchlist
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

class AddToWatchlistView(FormView):
    def post(self, request, *args, **kwargs):
        auction_id = self.kwargs['auction_id']
        auction = get_object_or_404(Auction, pk=auction_id)

        if Watchlist.objects.filter(user=request.user, auction=auction).exists():
            messages.error(request, "This auction is already in your watchlist.")
        else:
            Watchlist.objects.create(user=request.user, auction=auction)
            messages.success(request, "Auction added to your watchlist.")

        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

class WatchlistDeleteView(DeleteView):
    model = Watchlist
    success_url = reverse_lazy('watchlist')
    template_name = 'watchlist/removed_from_watchlist.html'

    def dispatch(self, request, *args, **kwargs):
        self.object = get_object_or_404(Watchlist, pk=self.kwargs['pk'])
        if not request.user.is_authenticated or self.object.user != request.user:
            return redirect('watchlist')

        response = super().dispatch(request, *args, **kwargs)
        messages.success(request, "Item removed from your watchlist.")
        return HttpResponseRedirect(self.success_url)