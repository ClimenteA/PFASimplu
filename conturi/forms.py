from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django import forms


class EmailAuthenticationForm(AuthenticationForm):
    """Formularul de login inclus in Django, cu email in loc de username."""

    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"autofocus": True, "autocomplete": "email"}),
    )


class EmailUserCreationForm(UserCreationForm):
    """Formularul de inregistrare inclus in Django (UserCreationForm),
    cu email-ul obligatoriu si unic, folosit ca username."""

    email = forms.EmailField(label="Email", max_length=254)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("email",)

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(username__iexact=email).exists():
            raise forms.ValidationError("Exista deja un cont cu acest email.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = user.email
        if commit:
            user.save()
        return user
