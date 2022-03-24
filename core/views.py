import logging

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.views import generic, View

from .forms import AuthForm

logger = logging.getLogger(__name__)


class RegistrationView(generic.edit.CreateView):
    form_class = AuthForm
    success_url = '/home/'
    template_name = 'forms.html'

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs['title'] = "Register"
        return kwargs


class LoginView(View):
    template_name = 'forms.html'
    form_class = AuthForm

    def get(self, request):
        form = self.form_class(auto_id=False)
        return render(request, 'forms.html', context={
            'form': form,
            'title': 'Login'
        })

    def post(self, request):
        try:
            user = authenticate(request=request, email=request.POST['email'], password=request.POST['password'])
            if user is not None:
                login(request, user)
                messages.success(request, 'Login successful')
                return redirect('home')
            return redirect('temp-login')
        except Exception as e:
            logger.exception(e)
            return redirect('temp-login')


def logout_view(request):
    logout(request)
    messages.warning(request, 'Logged out')
    return redirect('temp-login')
