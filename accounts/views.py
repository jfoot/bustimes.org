from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, render

from . import forms

UserModel = get_user_model()


def register(request):
    if settings.DISABLE_REGISTRATION:
        return render(
            request,
            "403.html",
            {
                "exception": "Registration is temporarily closed. Sorry. Please don't @ me",
            },
            status=503,
        )

    if request.method == "POST":
        form = forms.RegistrationForm(request.POST)
        if form.is_valid():
            form.save(request=request)
    else:
        form = forms.RegistrationForm()

    return render(
        request,
        "register.html",
        {
            "form": form,
        },
    )


class RegisterConfirmView(auth_views.PasswordResetConfirmView):
    pass


class LoginView(auth_views.LoginView):
    form_class = forms.LoginForm


class PasswordResetView(auth_views.PasswordResetView):
    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)
        context_data["form"].fields["email"].label = "Email address"
        return context_data


@login_required
def user_detail(request, pk):
    user = get_object_or_404(UserModel, pk=pk)

    if user.trusted is False and not request.user.is_superuser:
        revisions = None
    else:
        revisions = user.vehiclerevision_set.select_related(
            "vehicle", "from_livery", "to_livery", "from_type", "to_type"
        ).prefetch_related("vehiclerevisionfeature_set__feature")
        revisions = revisions.order_by("-id")
        paginator = Paginator(revisions, 100)
        page = request.GET.get("page")
        revisions = paginator.get_page(page)

    if request.user == user or request.user.is_superuser:
        initial = {
            "trusted": user.trusted,
            "username": user.username if user.username != user.email else "",
        }

        form = forms.UserForm(request.POST or None, initial=initial)
        if not request.user.is_superuser:
            del form.fields["trusted"]

        if request.POST and form.is_valid():
            if "delete" in request.POST:
                assert request.user == user
                user.is_active = False
                user.save(update_fields=["is_active"])
            elif "username" in form.cleaned_data:
                user.username = form.cleaned_data["username"]
                if not user.username:
                    user.username = user.email
                try:
                    user.save(update_fields=["username"])
                except IntegrityError:
                    form.add_error("username", "Username taken")
                    user.username = initial["username"] or user.email
            else:
                assert request.user.is_superuser
                user.trusted = form.cleaned_data["trusted"]
                user.save(update_fields=["trusted"])

    else:
        form = None

    return render(
        request,
        "user_detail.html",
        {"object": user, "revisions": revisions, "form": form},
    )
