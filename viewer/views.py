from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from decimal import Decimal

from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect, Http404
from django.contrib import messages
from django.contrib.auth import logout, login
from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import CharField, TextField, DateTimeField, ForeignKey, Q, BooleanField, Case, When
from django.shortcuts import render, redirect
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import FormView, ListView, TemplateView
from viewer.forms import SignUpForm, AuctionCreateForm, ProfileEditForm, BidForm, PurchaseForm
from django.views.generic import FormView, ListView, TemplateView, UpdateView, DeleteView, DetailView
from viewer.forms import SignUpForm, AuctionCreateForm, ProfileEditForm, BidForm, WatchlistForm, AuctionUpdateForm
from django.urls import reverse_lazy, reverse
from viewer.models import Watchlist, Auction, User, Profile, Bid, Category
from django.contrib.auth.forms import UserChangeForm
from viewer.models import Watchlist, Auction, User, Profile, Bid, Purchase


def index(request):
    value = request.GET.get('value', '')
    main_categories = Category.objects.filter(parent__isnull=True)  # only main categories
    return render(request, template_name='index.html', context={'value': value, 'main_categories': main_categories})


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

        #Filtering only auctions in "running" status
        queryset = queryset.filter(status="Running")

        #Filtered by category
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(categories__name__icontains=search_query)
            ).distinct()

        #Filtered by category
        if category_id:
            queryset = queryset.filter(categories__id=category_id)

        # Premium auctions priority
        queryset = queryset.annotate(
            is_premium_user=Case(
                When(seller__profile__is_premium=True, then=True),
                default=False,
                output_field=BooleanField(),
            )
        ).order_by('-is_premium_user', '-start_time')

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
        if categories:  # Ensure categories are not empty
            auction.categories.set(categories)

        return super().form_valid(form)

class AuctionSearchView(ListView):
    template_name = 'advanced_search.html'
    model = Auction
    context_object_name = 'auctions'
    paginate_by = 10  # numbers of auctions per page

    def get_queryset(self):
        query = self.request.GET.get('q', '')
        auctions = Auction.objects.all()
        status = self.request.GET.get('status')  # gets status from GET parameter

        # Filtering by user task (keyword)
        if query:
            auctions = auctions.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(categories__name__icontains=query) |
                Q(seller__username__icontains=query)
            ).distinct()

        # Filtering by status
        if status:
            auctions = auctions.filter(status=status)

        # Filtering by main category
        main_category = self.request.GET.get('main_category')
        if main_category:
            auctions = auctions.filter(categories__parent__isnull=True, categories__id=main_category)

        # Filtering by subcategory
        sub_category = self.request.GET.get('sub_category')
        if sub_category:
            auctions = auctions.filter(categories__id=sub_category)

        # Premium auctions priority
        auctions = auctions.annotate(
            is_premium=Case(
                When(seller__profile__is_premium=True, then=True),
                default=False,
                output_field=BooleanField(),
            )
        ).order_by('-is_premium', '-start_time')

        # Filtering by city and end_time
        city = self.request.GET.get('city')
        if city:
            auctions = auctions.filter(seller__profile__city__icontains=city)

        # Sorting by end_time or start_time
        sort_by = self.request.GET.get('sort_by')
        if sort_by == 'end_time':
            auctions = auctions.order_by('end_time')
        elif sort_by == 'start_time':
            auctions = auctions.order_by('-start_time')

        return auctions

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['auction_status'] = Auction.STATUS_CHOICES
        context['categories'] = Category.objects.select_related('parent').all()
        main_category = self.request.GET.get('main_category')

    #Filter categories for subcategory dropdown after selected main_category
        if main_category:
            context['sub_categories'] = Category.objects.filter(parent_id=main_category)
        else:
            context['sub_categories'] = Category.objects.none()

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
        queryset = Auction.objects.filter(seller=self.request.user)

        # Filtration by status of auction ("Running", "Closed" ...)
        status_filter = self.request.GET.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)

class AuctionUpdateView(UpdateView):
    template_name = 'auction_update.html'
    form_class = AuctionUpdateForm
    model = Auction
    success_url = reverse_lazy('my_auctions')

    def dispatch(self, request, *args, **kwargs):
        auction = self.get_object() #gets the auction instance by pk from URL
        if auction.seller != request.user: #check if the user is seller
            raise PermissionDenied("You do not have permission to edit this auction.")
        return super().dispatch(request, *args, **kwargs)

class AuctionCancelView(View):
    model = Auction
    template_name = 'auction_cancel.html'
    success_url = reverse_lazy('my_auctions')

    def get(self, request, pk):
        # Load auction by ID a user
        auction = get_object_or_404(Auction, pk=pk, seller=request.user)
        return render(request, self.template_name, {'object': auction})

    def post(self, request, pk):
        # Load auction by ID a user
        auction = get_object_or_404(Auction, pk=pk, seller=request.user)
        auction.status = Auction.CANCELLED  # change status auction to "Canceled"
        auction.save()
        messages.success(request, "Auction have been cancelled.")
        return redirect(self.success_url)

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