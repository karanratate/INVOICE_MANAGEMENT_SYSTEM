from django import forms
from .models import Invoice, InvoiceItem
from customers.models import Customer
from products.models import Product

class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['invoice_type', 'status', 'customer', 'issue_date', 'due_date', 
                  'discount', 'shipping', 'notes', 'custom_email_message']
        widgets = {
            'issue_date': forms.DateInput(attrs={'type': 'date'}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }

class InvoiceItemForm(forms.ModelForm):
    product = forms.ModelChoiceField(queryset=Product.objects.all(), required=False)
    
    class Meta:
        model = InvoiceItem
        fields = ['product', 'description', 'quantity', 'price', 'discount']