from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.contrib.auth.models import User
from invoices.models import Invoice
from products.models import Product
from customers.models import Customer


@login_required
def dashboard(request):
    # STRICT SEPARATION: Everyone (including Admin) only sees their own data here
    invoices = Invoice.objects.filter(owner=request.user)
    products = Product.objects.filter(owner=request.user)
    customers = Customer.objects.filter(owner=request.user)

    context = {
        # Invoices
        'total_invoices': invoices.count(),
        'pending_invoices': invoices.filter(status='open').count(),
        'paid_invoices': invoices.filter(status='paid').count(),
        'total_sales': invoices.filter(status='paid').aggregate(Sum('total'))['total__sum'] or 0,
        'total_due': invoices.filter(status='open').aggregate(Sum('total'))['total__sum'] or 0,
        
        # Products & Customers
        'total_products': products.count(),
        'total_customers': customers.count(),
        
        # Recent Invoices (Filtered)
        'recent_invoices': invoices.order_by('-created_at')[:5],
    }

    # Admin still gets the total user count (since only Admin can manage users)
    if request.user.is_superuser:
        context['total_users'] = User.objects.count()

    return render(request, 'core/dashboard.html', context)