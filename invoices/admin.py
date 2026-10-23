from django.contrib import admin
from .models import Invoice, InvoiceItem

class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1
    fields = ['product', 'description', 'quantity', 'price', 'discount', 'subtotal']
    readonly_fields = ['subtotal']

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'customer', 'status', 'total', 'issue_date', 'due_date']
    search_fields = ['invoice_number', 'customer__name', 'customer__email']
    list_filter = ['status', 'invoice_type', 'issue_date']
    readonly_fields = ['created_at', 'updated_at', 'subtotal', 'total', 'vat']
    inlines = [InvoiceItemInline]
    fieldsets = (
        ('Invoice Information', {
            'fields': ('invoice_number', 'invoice_type', 'status', 'customer')
        }),
        ('Dates', {
            'fields': ('issue_date', 'due_date')
        }),
        ('Financial', {
            'fields': ('subtotal', 'discount', 'shipping', 'vat', 'total')
        }),
        ('Additional', {
            'fields': ('notes', 'custom_email_message')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )