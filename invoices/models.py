from django.db import models
from django.conf import settings
from customers.models import Customer
from django.contrib.auth.models import User
from decimal import Decimal


class Invoice(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ]
    
    TYPE_CHOICES = [
        ('invoice', 'Invoice'),
        ('quote', 'Quote'),
        ('receipt', 'Receipt'),
    ]
    
    invoice_number = models.CharField(max_length=50)  # Removed unique=True
    invoice_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='invoice')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # ADDED OWNER FIELD (Multi-tenant support)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='invoices')
    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='invoices')
    issue_date = models.DateField()
    due_date = models.DateField()
    
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    shipping = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    vat = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    notes = models.TextField(blank=True)
    custom_email_message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.invoice_number} - {self.customer.name}"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Invoice'
        verbose_name_plural = 'Invoices'
        # Ensure invoice numbers are unique per user
        unique_together = ('invoice_number', 'owner')


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.SET_NULL,
        null=True, blank=True
    )
    description = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.CharField(max_length=50, default='0', blank=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    def __str__(self):
        return f"{self.invoice.invoice_number} - {self.description}"
    
    def save(self, *args, **kwargs):
        # Always convert to Decimal before doing math
        price = Decimal(str(self.price)) if self.price is not None else Decimal('0')
        quantity = Decimal(str(self.quantity)) if self.quantity is not None else Decimal('0')
        
        item_subtotal = price * quantity
        
        # Handle discount safely
        discount_value = self.discount
        if discount_value:
            discount_str = str(discount_value).strip()
            try:
                if '%' in discount_str:
                    percent = Decimal(discount_str.replace('%', '').strip())
                    discount_amount = item_subtotal * (percent / Decimal('100'))
                else:
                    discount_amount = Decimal(discount_str)
                item_subtotal -= discount_amount
            except Exception:
                pass
        
        self.subtotal = item_subtotal
        super().save(*args, **kwargs)