from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth import logout, login
from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect
from django.db.models import CharField, TextField, DateTimeField, ForeignKey
from django.views.generic import FormView, ListView, TemplateView, UpdateView, DeleteView, View
from viewer.forms import SignUpForm, AuctionCreateForm, UserCreationForm, ModelForm, ProfileEditForm
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


class ProfileEditView(View):
    template_name = 'profile_edit.html'
    form_class = ProfileEditForm
    success_url = reverse_lazy('profile')

    def get(self, request, *args, **kwargs):
        form = self.form_class(instance=request.user.profile)
        return render(request, self.template_name, {'form': form})  # Použijte render místo render_to_response

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            return redirect(self.success_url)
        return render(request, self.template_name, {'form': form})  # Opět použijte render

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/login')  # Přesměrování na login, pokud není uživatel přihlášen
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
        result = super().form_valid(form)
        cleaned_data = form.cleaned_data
        auction = Auction.objects.create(
            name=cleaned_data['name'],
            description=cleaned_data['description'],
            starting_price=cleaned_data['starting_price'],
            start_time=cleaned_data['start_time'],
            end_time=cleaned_data['end_time'],
        )
        categories = form.cleaned_data['categories']
        auction.categories.set(categories)

        return super().form_valid(form)


class WatchlistView(ListView):
    template_name = "watchlist.html"
    model = Watchlist

    def get_queryset(self):
        return Watchlist.objects.filter(user=self.request.user)

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)