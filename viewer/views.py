from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth import logout, login
from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect
from django.db.models import CharField, TextField, DateTimeField, ForeignKey
from django.views.generic import FormView, ListView, TemplateView, UpdateView, DeleteView
from viewer.forms import SignUpForm
from django.urls import reverse_lazy
from viewer.models import Auction, Watchlist

# from .models import Auction



def index(request):
    value = request.GET.get('value', '')
    return render(request, template_name='index.html', context={'value': value})

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'

    def form_invalid(self, form):
        messages.error(self.request, "Wrong username or password")
        # messages.success(self.request, "Přihlášení se podařilo")
        print("Error: wrong login")  # Přidej log pro kontrolu
        return super().form_invalid(form)

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('/')
        return super().dispatch(request, *args, **kwargs)

class ProfileView(TemplateView):
    template_name = 'profile.html'

class RegisterView(FormView):
    template_name = 'registration/register.html'
    form_class = SignUpForm
    success_url = reverse_lazy('profile')

    # @login_required
    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect(self.success_url)

    def for_invalid(self, form):
        messages.error(self.request, form.errors)
        return super().form_invalid(form)


class AuctionView(ListView):
    model = Auction
    template_name = 'auctions.html'
    context_object_name = 'auctions'

class WatchlistView(ListView):
    template_name = "watchlist.html"
    model = Watchlist

    def get_queryset(self):
        return Watchlist.objects.filter(user=self.request.user)

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)