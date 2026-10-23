from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from decimal import Decimal, InvalidOperation
from .models import Product


def to_decimal(value, default='0'):
    """Safely convert value to Decimal."""
    try:
        if value is None or value == '':
            return Decimal(default)
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal(default)



# 1. PRODUCT LIST

@login_required
def product_list(request):
    # STRICT ISOLATION: Everyone (including Admin) sees ONLY their own products
    products = Product.objects.filter(owner=request.user).order_by('name')
    
    paginator = Paginator(products, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'products/product_list.html', {'page_obj': page_obj})



# 2. PRODUCT CREATE

@login_required
def product_create(request):
    if request.method == 'POST':
        try:
            name = request.POST.get('product_name', '').strip()
            desc = request.POST.get('product_desc', '').strip()
            price = to_decimal(request.POST.get('product_price', '0'))

            if not name:
                messages.error(request, 'Product name is required!')
                return redirect('products:product_create')

            if price <= 0:
                messages.error(request, 'Price must be greater than 0!')
                return redirect('products:product_create')

            Product.objects.create(
                name=name,
                description=desc,
                price=price,
                owner=request.user  #  Assign owner
            )

            messages.success(request, f'Product "{name}" created successfully!')
            return redirect('products:product_list')

        except Exception as e:
            import traceback
            traceback.print_exc()
            messages.error(request, f'Error creating product: {str(e)}')
            return redirect('products:product_create')

    return render(request, 'products/product_create.html')


# 3. PRODUCT EDIT

@login_required
def product_edit(request, pk):
    # STRICT ISOLATION: Only allow edit if the user owns it
    product = get_object_or_404(Product, pk=pk, owner=request.user)

    if request.method == 'POST':
        try:
            name = request.POST.get('product_name', '').strip()
            desc = request.POST.get('product_desc', '').strip()
            price = to_decimal(request.POST.get('product_price', '0'))

            if not name:
                messages.error(request, 'Product name is required!')
                return redirect('products:product_edit', pk=pk)

            if price <= 0:
                messages.error(request, 'Price must be greater than 0!')
                return redirect('products:product_edit', pk=pk)

            product.name = name
            product.description = desc
            product.price = price
            product.save()

            messages.success(request, f'Product "{name}" updated successfully!')
            return redirect('products:product_list')

        except Exception as e:
            import traceback
            traceback.print_exc()
            messages.error(request, f'Error updating product: {str(e)}')

    return render(request, 'products/product_edit.html', {'product': product})


# 4. PRODUCT DELETE

@login_required
def product_delete(request, pk):
    # STRICT ISOLATION: Only allow delete if the user owns it
    product = get_object_or_404(Product, pk=pk, owner=request.user)

    if request.method == 'POST':
        try:
            name = product.name
            product.delete()
            messages.success(request, f'Product "{name}" deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error deleting product: {str(e)}')

    return redirect('products:product_list')