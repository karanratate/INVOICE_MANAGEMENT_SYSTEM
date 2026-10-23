from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Customer


# 1. CUSTOMER LIST


@login_required
def customer_list(request):
    # STRICT ISOLATION: Everyone (including Admin) sees ONLY their own customers
    customers = Customer.objects.filter(owner=request.user).order_by('-created_at')
    
    paginator = Paginator(customers, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'customers/customer_list.html', {'page_obj': page_obj})


# 2. CUSTOMER CREATE

@login_required
def customer_create(request):
    if request.method == 'POST':
        try:
            name = request.POST.get('name', '').strip()
            email = request.POST.get('email', '').strip()

            if not name:
                messages.error(request, 'Customer name is required!')
                return redirect('customers:customer_create')

            if not email:
                messages.error(request, 'Customer email is required!')
                return redirect('customers:customer_create')

            # Check duplicate email ONLY for this user
            if Customer.objects.filter(email=email, owner=request.user).exists():
                messages.error(request, f'A customer with email "{email}" already exists!')
                return redirect('customers:customer_create')

            customer = Customer.objects.create(
                name=name,
                email=email,
                phone=request.POST.get('phone', '').strip(),
                address_line1=request.POST.get('address_line1', '').strip(),
                address_line2=request.POST.get('address_line2', '').strip(),
                city=request.POST.get('city', '').strip(),
                state=request.POST.get('state', '').strip(),
                postal_code=request.POST.get('postal_code', '').strip(),
                country=request.POST.get('country', '').strip(),
                shipping_name=request.POST.get('shipping_name', '').strip(),
                shipping_address_line1=request.POST.get('shipping_address_line1', '').strip(),
                shipping_address_line2=request.POST.get('shipping_address_line2', '').strip(),
                shipping_city=request.POST.get('shipping_city', '').strip(),
                shipping_state=request.POST.get('shipping_state', '').strip(),
                shipping_postal_code=request.POST.get('shipping_postal_code', '').strip(),
                shipping_country=request.POST.get('shipping_country', '').strip(),
                owner=request.user  # Assign owner
            )

            messages.success(request, f'Customer "{name}" created successfully!')
            return redirect('customers:customer_list')

        except Exception as e:
            import traceback
            traceback.print_exc()
            messages.error(request, f'Error creating customer: {str(e)}')
            return redirect('customers:customer_create')

    return render(request, 'customers/customer_create.html')


# 3. CUSTOMER EDIT

@login_required
def customer_edit(request, pk):
    # STRICT ISOLATION: Only allow edit if the user owns it
    customer = get_object_or_404(Customer, pk=pk, owner=request.user)

    if request.method == 'POST':
        try:
            name = request.POST.get('name', '').strip()
            email = request.POST.get('email', '').strip()

            if not name:
                messages.error(request, 'Customer name is required!')
                return redirect('customers:customer_edit', pk=pk)

            if not email:
                messages.error(request, 'Customer email is required!')
                return redirect('customers:customer_edit', pk=pk)

            # Check duplicate email (excluding current customer) ONLY for this user
            if Customer.objects.filter(email=email, owner=request.user).exclude(pk=pk).exists():
                messages.error(request, f'Another customer with email "{email}" already exists!')
                return redirect('customers:customer_edit', pk=pk)

            customer.name = name
            customer.email = email
            customer.phone = request.POST.get('phone', '').strip()
            customer.address_line1 = request.POST.get('address_line1', '').strip()
            customer.address_line2 = request.POST.get('address_line2', '').strip()
            customer.city = request.POST.get('city', '').strip()
            customer.state = request.POST.get('state', '').strip()
            customer.postal_code = request.POST.get('postal_code', '').strip()
            customer.country = request.POST.get('country', '').strip()
            customer.shipping_name = request.POST.get('shipping_name', '').strip()
            customer.shipping_address_line1 = request.POST.get('shipping_address_line1', '').strip()
            customer.shipping_address_line2 = request.POST.get('shipping_address_line2', '').strip()
            customer.shipping_city = request.POST.get('shipping_city', '').strip()
            customer.shipping_state = request.POST.get('shipping_state', '').strip()
            customer.shipping_postal_code = request.POST.get('shipping_postal_code', '').strip()
            customer.shipping_country = request.POST.get('shipping_country', '').strip()

            customer.save()

            messages.success(request, f'Customer "{name}" updated successfully!')
            return redirect('customers:customer_list')

        except Exception as e:
            import traceback
            traceback.print_exc()
            messages.error(request, f'Error updating customer: {str(e)}')

    return render(request, 'customers/customer_edit.html', {'customer': customer})



# 4. CUSTOMER DELETE

@login_required
def customer_delete(request, pk):
    # STRICT ISOLATION: Only allow delete if the user owns it
    customer = get_object_or_404(Customer, pk=pk, owner=request.user)

    if request.method == 'POST':
        try:
            name = customer.name
            customer.delete()
            messages.success(request, f'Customer "{name}" deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error deleting customer: {str(e)}')

    return redirect('customers:customer_list')