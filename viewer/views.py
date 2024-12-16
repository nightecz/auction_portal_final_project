from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth import logout, login
from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect
from django.db.models import CharField, TextField, DateTimeField, ForeignKey
from django.views import View
from django.views.generic import FormView, ListView, TemplateView, UpdateView, DeleteView, DetailView
from viewer.forms import SignUpForm, AuctionCreateForm, ProfileEditForm
from django.urls import reverse_lazy
from viewer.models import Watchlist, Auction, User, Profile
from django.contrib.auth.forms import UserChangeForm

def index(request):
    value = request.GET.get('value', '')
    return render(request, template_name='index.html', context={'value': value})

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

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/login')
        return super().dispatch(request, *args, **kwargs)



class RegisterView(FormView):
    template_name = 'registration/register.html'
    form_class = SignUpForm
    success_url = reverse_lazy('profile')

    # @login_required
    def form_valid(self, form):
        user = form.save()
        Profile.objects.create(user=user)
        login(self.request, user)
        return redirect(self.success_url)

    def for_invalid(self, form):
        messages.error(self.request, form.errors)
        return super().form_invalid(form)


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
    model = Auction
    template_name = 'auction_detail.html'
    context_object_name = 'auction'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['auction'] = Auction.objects.get(pk=kwargs['id'])
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


class WatchlistView(ListView):
    template_name = "watchlist/watchlist.html"
    model = Watchlist

    def get_queryset(self):
        return Watchlist.objects.filter(user=self.request.user)

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)

def check_if_auction_is_in_watchlist(user, movie):
    return Watchlist.objects.filter(user=user, auction=auction).exists()

def watchlist_add(request):
    movie_id = request.GET.get('movie')
    check_if_auction_is_in_watchlist(request.user, Auction.objects.get(pk=auction_id))
    if check_if_auction_is_in_watchlist(request.user, Auction.objects.get(pk=auction_id)):
        return redirect('watchlist/watchlist')
    else:
        Watchlist.objects.create(
            user=request.user,
            movie=Auction.objects.get(pk=auction_id)
        )

    return redirect('watchlist')