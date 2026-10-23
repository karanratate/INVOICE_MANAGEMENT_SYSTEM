from django.contrib import admin
from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'email', 'phone', 'city', 'country', 'created_at']
    search_fields = ['name', 'email', 'phone', 'city']
    list_filter = ['country', 'state']
    ordering = ['-created_at']
    list_per_page = 20