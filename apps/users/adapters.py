from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model
import re

User = get_user_model()


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        if sociallogin.is_existing:
            return

        email = sociallogin.account.extra_data.get('email', '')
        if not email:
            return

        try:
            user = User.objects.get(email=email)
            sociallogin.connect(request, user)
        except User.DoesNotExist:
            pass

    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)

        extra = sociallogin.account.extra_data
        email = extra.get('email', '')
        if not user.username:
            base_username = re.sub(r'[^a-zA-Z0-9_]', '', extra.get('given_name', email.split('@')[0] if email else 'user'))
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            user.username = username

        user.email = extra.get('email', user.email)
        user.first_name = extra.get('given_name', '')
        user.last_name = extra.get('family_name', '')

        return user
