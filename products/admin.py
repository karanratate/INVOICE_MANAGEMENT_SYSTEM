from django.contrib import admin
from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'price', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']
    list_per_page = 20