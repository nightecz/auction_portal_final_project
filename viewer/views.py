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
from django.db.models import CharField, TextField, DateTimeField, ForeignKey, Q, BooleanField, Case, When, Avg
from django.shortcuts import render, redirect
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import FormView, ListView, TemplateView
from viewer.forms import SignUpForm, AuctionCreateForm, ProfileEditForm, BidForm, PurchaseForm, ReviewForm
from django.views.generic import FormView, ListView, TemplateView, UpdateView, DeleteView, DetailView
from viewer.forms import SignUpForm, AuctionCreateForm, ProfileEditForm, BidForm, WatchlistForm, AuctionUpdateForm
from django.urls import reverse_lazy, reverse
from viewer.models import Watchlist, Auction, User, Profile, Bid, Category, Review, Purchase
from django.contrib.auth.forms import UserChangeForm


def index(request):
    value = request.GET.get('value', '')
    main_categories = Category.objects.filter(parent__isnull=True)  # only main categories
    recent_auctions = Auction.objects.filter(status="Running").order_by('-start_time')[:4]  # showing recently added auctions
    ending_soon_auctions = Auction.objects.filter(status="Running", end_time__gt=timezone.now()).order_by('end_time')[:4] # ending soon auctions
    ended_auctions = Auction.objects.filter(status__in=["Closed", "Sold"]).order_by('-end_time')[:4]

    unconfirmed_sales_count = 0
    if request.user.is_authenticated:
        user_profile = request.user.profile
        unconfirmed_sales = Purchase.objects.filter(seller=user_profile, seller_confirmation=False)
        unconfirmed_sales_count = unconfirmed_sales.count()

    unconfirmed_purchases_count = 0
    if request.user.is_authenticated:
        user_profile = request.user.profile
        unconfirmed_purchases = Purchase.objects.filter(buyer=user_profile, buyer_confirmation=False)
        unconfirmed_purchases_count = unconfirmed_purchases.count()

    return render(request, 'index.html', {
        'value': value,
        'main_categories': main_categories,
        'recent_auctions': recent_auctions,
        'ending_soon_auctions': ending_soon_auctions,
        'ended_auctions': ended_auctions,
        'unconfirmed_sales_count': unconfirmed_sales_count,
        'unconfirmed_purchases_count': unconfirmed_purchases_count
    })


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
        #Gets data from form
        print("Form cleaned_data:", form.cleaned_data)

        auction = form.save(commit=False)
        auction.seller = self.request.user
        auction.save()

        categories = form.cleaned_data['categories']
        subcategories = form.cleaned_data['subcategories']

        if categories:  # Ensure categories are not empty
            auction.categories.set(categories)
        if subcategories:  # Subcategories, if they are choose
            auction.categories.add(*subcategories)

        return super().form_valid(form)

class AuctionSearchView(ListView):
    template_name = 'advanced_search.html'
    model = Auction
    context_object_name = 'auctions'
    paginate_by = 10  # numbers of auctions per page

    def get_queryset(self):
        query = self.request.GET.get('q', '')
        auctions = Auction.objects.all()
        status = self.request.GET.get('status', 'Running')  # gets status from GET parameter, default in search is status 'Running'

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

from django.utils import timezone

class UserSearchView(ListView):
    template_name = 'user_search.html'
    model = Profile
    context_object_name = 'profiles'
    paginate_by = 20  # numbers of auctions per page

    def get_queryset(self):
        profiles = Profile.objects.all()

        profiles = profiles.annotate(average_rating=Avg('received_reviews__rating'))

        # filtering by username (keyword)
        query = self.request.GET.get('q', '').strip()
        if query:
            profiles = profiles.filter(
                Q(user__username__icontains=query))

        # filtering by average score
        min_average_rating = self.request.GET.get('average_rating')
        if min_average_rating:
            try:
                min_average_rating = float(min_average_rating)
                profiles = profiles.filter(average_rating__gte=min_average_rating)
            except ValueError:
                pass  # if number is not valit, filtr ignore


        # sorting by average score
        sort_by = self.request.GET.get('sort_by', '-average_rating')  # default sorting
        if sort_by in ['average_rating', '-average_rating']:
            profiles = profiles.order_by(sort_by)
        return profiles

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['average_rating'] = self.request.GET.get('average_rating', '')
        return context

class AuctionDetailView(TemplateView):
    template_name = 'auction_detail.html'
    context_object_name = 'auction'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        auction_id = self.kwargs.get('id')
        auction = Auction.objects.get(pk=auction_id)
        context['auction'] = auction

        if self.request.user.is_authenticated:
            user_watchlist = Watchlist.objects.filter(user=self.request.user)
            auction_ids_in_watchlist = user_watchlist.values_list('auction_id', flat=True)
            context['auction_ids_in_watchlist'] = auction_ids_in_watchlist
        else:
            context['auction_ids_in_watchlist'] = []


        try:
            purchase = Purchase.objects.get(auction=auction)
        except Purchase.DoesNotExist:
            purchase = None

        def close_auction_and_create_purchase(auction):
            if auction.status == Auction.CLOSED and not auction.purchases.exists():
                if auction.bids.exists():
                    highest_bid = auction.bids.latest('created_at')

                    purchase = Purchase.objects.create(
                        auction=auction,
                        buyer=highest_bid.bidder.profile,
                        seller=auction.seller.profile,
                        winning_price=highest_bid.amount
                    )
                    purchase.save()

                    auction.purchase = purchase
                    auction.save()

                    auction.status = Auction.CLOSED
                    auction.save()

                    return purchase
            return None

        if auction.end_time < timezone.now() and auction.status == Auction.RUNNING:
            auction.status = Auction.CLOSED
            auction.save()


            purchase = close_auction_and_create_purchase(auction)

        context['purchase'] = purchase
        context['current_time'] = timezone.now()

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

class AuctionRelistView(View):
    model = Auction
    template_name = 'auction_relist.html'
    success_url = reverse_lazy('my_auctions')
    form_class = AuctionCreateForm

    def get_object(self):
        # Load auction by (pk) from URL
        pk = self.kwargs.get('pk')
        return get_object_or_404(self.model, pk=pk)

    def dispatch(self, request, *args, **kwargs):
        auction = self.get_object()

        # Check for 'Closed' or 'Cancelled'
        if auction.status not in [Auction.CLOSED, Auction.CANCELLED]:
            messages.error(request, "Only closed or cancelled auction could be relisted.")
            return redirect(self.success_url)

        # Check for seller = owner
        if auction.seller != request.user:
            messages.error(request, "You do not have right to do that.")
            return redirect(self.success_url)

        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        # Gets auction by pk
        auction = self.get_object()

        # Proceed data from form
        form = self.form_class(request.POST, instance=auction)

        if form.is_valid():
            auction = form.save(commit=False)

            # Update status and time
            auction.status = Auction.RUNNING
            auction.start_time = timezone.now()
            auction.end_time = form.cleaned_data.get('end_time')

            auction.save()

            messages.success(request, "Auction has been relisted.")
            return redirect(self.success_url)
        else:
            messages.error(request, "There was an error relisting the auction.")
            return render(request, self.template_name, {'form': form, 'auction': auction})

@method_decorator(login_required, name='dispatch')
class AuctionBiddingView(ListView):
    template_name = "auctions/bidding.html"
    model = Auction
    context_object_name = "auctions"

    def get_queryset(self):
        # getting auctions by bids, where user is also bidder
        return Auction.objects.filter(bids__bidder=self.request.user).distinct()

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

        last_bid = auction.bids.order_by('-created_at').first()
        if last_bid and last_bid.bidder == request.user:
            messages.error(request, "You cannot place another bid until someone else bids.")
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
    def post(self, request, *args, **kwargs):
        purchase_id = self.kwargs.get('purchase_id')
        try:
            purchase = Purchase.objects.get(id=purchase_id)
        except Purchase.DoesNotExist:
            messages.error(request, "Purchase not found.")
            return redirect('auction_detail', id=purchase.auction.id)

        if purchase.auction.seller.profile != request.user.profile:
            messages.error(request, "You are not authorized to confirm the sale.")
            return redirect('auction_detail', id=purchase.auction.id)

        purchase.seller_confirmation = True
        purchase.save()

        purchase.auction.status = Auction.SOLD
        purchase.auction.save()

        return redirect('contact_info', purchase_id=purchase.id)



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


class ContactInfoView(View):
    def get(self, request, *args, **kwargs):
        purchase_id = self.kwargs.get('purchase_id')
        try:
            purchase = Purchase.objects.get(id=purchase_id)
        except Purchase.DoesNotExist:
            messages.error(request, "Purchase not found.")
            return redirect('index')

        buyer_contact_info = {
            'name': f"{purchase.buyer.first_name} {purchase.buyer.last_name}",
            'email': purchase.buyer.user.email,
            'phone': purchase.buyer.phone,
            'street': purchase.buyer.street,
            'house_number': purchase.buyer.house_number,
            'city': purchase.buyer.city,
            'zip_code': purchase.buyer.zip_code,
            'country': purchase.buyer.country
        }

        print(f"Buyer Contact Info: {buyer_contact_info}")  # Přidání ladicího výstupu

        context = {
            'purchase': purchase,
            'buyer_contact_info': buyer_contact_info
        }

        return render(request, 'contact_info.html', context)

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/')
        return super().dispatch(request, *args, **kwargs)


class ReviewCreateView(FormView):
    model = Review
    template_name = 'review_form.html'
    form_class = ReviewForm
    success_url = reverse_lazy('my_auctions')

    # Get the purchase id from the URL and then get the purchase object and pass it to the form
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        purchase_id = self.request.GET.get('purchase')
        context['purchase'] = Purchase.objects.get(pk=purchase_id)
        return context

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        cleaned_data = form.cleaned_data
        purchase_id = self.request.GET.get('purchase')
        purchase = Purchase.objects.get(pk=purchase_id)

        # conditions, who is writting the review
        if self.request.user.profile == purchase.buyer:
            reviewer = purchase.buyer
            reviewee = purchase.seller
        elif self.request.user.profile == purchase.seller:
            reviewer = purchase.seller
            reviewee = purchase.buyer
        else:
            return self.form_invalid(form)

        # check if review does not already exist
        existing_review = Review.objects.filter(
            Q(reviewer=reviewer) & Q(purchase=purchase)
        ).exists()

        if existing_review:
            form.add_error(None, "You have already written a review for this purchase.")
            return self.form_invalid(form)

        # create review
        Review.objects.create(
            reviewer=reviewer,
            reviewee=reviewee,
            purchase=purchase,
            rating=cleaned_data['rating'],
            text=cleaned_data['text']
            )

        # average rating calculation
        purchase.seller.calculate_average_rating()
        return super().form_valid(form)


class WonAuctionsView(ListView):
    template_name = 'won_auctions.html'
    model = Auction
    context_object_name = 'auctions'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        purchase_id = self.request.GET.get('purchase')
        if purchase_id:
            context['purchase'] = Purchase.objects.get(pk=purchase_id)

        unconfirmed_purchase = Purchase.objects.filter(buyer=self.request.user.profile,
                                                       buyer_confirmation=False).first()
        if unconfirmed_purchase:
            context['unconfirmed_purchase'] = unconfirmed_purchase

        return context

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        won_auctions = Auction.objects.filter(status__in=[Auction.CLOSED, Auction.SOLD])
        won_auctions_by_user = won_auctions.filter(purchase__buyer=self.request.user.profile)

        return won_auctions_by_user


