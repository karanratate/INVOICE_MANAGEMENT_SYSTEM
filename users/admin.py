from django.contrib import admin
from django.contrib.admin.forms import AdminAuthenticationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

#  Force Django Admin to ONLY allow superusers
class CustomAdminAuthenticationForm(AdminAuthenticationForm):
    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not user.is_superuser:
            raise ValidationError(
                _("You do not have permission to access the Admin Panel."),
                code='no_permission',
            )

# Replace the default admin login form with our custom one
admin.site.login_form = CustomAdminAuthenticationForm