from django.shortcuts import render
from django.shortcuts import redirect
# Create your views here.
from allauth.account import views


class SigninView(views.LoginView):
    template_name = 'accounts/signin.html'

    def dispatch(self, request, *args, **kwargs):
        response = super(SigninView, self).dispatch(request, *args, **kwargs)
        return response

    def form_valid(self, form):
      return super(SigninView, self).form_valid(form)


signin_view = SigninView.as_view()


class SignupView(views.SignupView):
    template_name = 'accounts/signup.html'


signup_view = SignupView.as_view()


class SignoutView(views.LogoutView):

    def get(self, *args, **kwargs):
        return self.post(*args, **kwargs)

    def post(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            self.logout()
        return super(SignoutView, self).post(*args, **kwargs)


signout_view = SignoutView.as_view()



