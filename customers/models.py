from django.db import models
from django.core.validators import EmailValidator
from django.contrib.auth.models import User


class Customer(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField(validators=[EmailValidator()])
    phone = models.CharField(max_length=20, blank=True)
    
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    
    # Shipping address
    shipping_name = models.CharField(max_length=200, blank=True)
    shipping_address_line1 = models.CharField(max_length=255, blank=True)
    shipping_address_line2 = models.CharField(max_length=255, blank=True)
    shipping_city = models.CharField(max_length=100, blank=True)
    shipping_state = models.CharField(max_length=100, blank=True)
    shipping_postal_code = models.CharField(max_length=20, blank=True)
    shipping_country = models.CharField(max_length=100, blank=True)
    
    # ADDED OWNER FIELD (Multi-tenant support)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='customers')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Customer'
        verbose_name_plural = 'Customers'