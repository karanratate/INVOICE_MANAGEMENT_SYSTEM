from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.db import transaction
from django.core.paginator import Paginator
from django.conf import settings
from decimal import Decimal, InvalidOperation
from .models import Invoice, InvoiceItem
from products.models import Product
from customers.models import Customer
from .utils.pdf_generator import generate_invoice_pdf


# ============================================================
# HELPER: Safely convert values to Decimal
# ============================================================
def to_decimal(value, default='0'):
    """Safely convert any value to Decimal."""
    try:
        if value is None or value == '':
            return Decimal(default)
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal(default)


# ============================================================
# 1. INVOICE LIST
# ============================================================
@login_required
def invoice_list(request):
    # STRICT ISOLATION: Everyone sees ONLY their own invoices
    invoices = Invoice.objects.filter(owner=request.user).order_by('invoice_number')
        
    paginator = Paginator(invoices, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'invoices/invoice_list.html', {'page_obj': page_obj})


# ============================================================
# 2. INVOICE CREATE
# ============================================================
@login_required
def invoice_create(request):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # ----- Step 1: Customer data -----
                customer_name = request.POST.get('customer_name', '').strip()
                customer_email = request.POST.get('customer_email', '').strip()
                
                if not customer_name or not customer_email:
                    messages.error(request, 'Customer name and email are required!')
                    return redirect('invoices:invoice_create')
                
                # STRICT ISOLATION: Only find/create customer for THIS user
                customer = Customer.objects.filter(email=customer_email, owner=request.user).first()
                
                if not customer:
                    customer = Customer.objects.create(
                        email=customer_email,
                        owner=request.user,
                        name=customer_name,
                        phone=request.POST.get('customer_phone', ''),
                        address_line1=request.POST.get('customer_address_1', ''),
                        address_line2=request.POST.get('customer_address_2', ''),
                        city=request.POST.get('customer_town', ''),
                        state=request.POST.get('customer_county', ''),
                        postal_code=request.POST.get('customer_postcode', ''),
                        country=request.POST.get('customer_county', ''),
                        shipping_name=request.POST.get('customer_name_ship', ''),
                        shipping_address_line1=request.POST.get('customer_address_1_ship', ''),
                        shipping_address_line2=request.POST.get('customer_address_2_ship', ''),
                        shipping_city=request.POST.get('customer_town_ship', ''),
                        shipping_state=request.POST.get('customer_county_ship', ''),
                        shipping_postal_code=request.POST.get('customer_postcode_ship', ''),
                        shipping_country=request.POST.get('customer_county_ship', ''),
                    )
                else:
                    # Update existing customer details
                    customer.name = customer_name
                    customer.phone = request.POST.get('customer_phone', '')
                    customer.address_line1 = request.POST.get('customer_address_1', '')
                    customer.address_line2 = request.POST.get('customer_address_2', '')
                    customer.city = request.POST.get('customer_town', '')
                    customer.state = request.POST.get('customer_county', '')
                    customer.postal_code = request.POST.get('customer_postcode', '')
                    customer.save()
                
                # ----- Step 2: Invoice number -----
                #  STRICT ISOLATION: Only look at invoices belonging to THIS user
                last_invoice = Invoice.objects.filter(owner=request.user).order_by('-id').first()
                    
                if last_invoice:
                    try:
                        last_num = int(''.join(filter(str.isdigit, last_invoice.invoice_number)))
                        next_num = last_num + 1
                    except Exception:
                        next_num = Invoice.objects.filter(owner=request.user).count() + 1
                else:
                    next_num = 1
                
                invoice_number = f"{settings.INVOICE_PREFIX}{next_num:02d}"
                
                # ----- Step 3: Dates -----
                issue_date = request.POST.get('invoice_date')
                due_date = request.POST.get('invoice_due_date')
                
                if not issue_date or not due_date:
                    messages.error(request, 'Issue date and due date are required!')
                    return redirect('invoices:invoice_create')
                
                # ----- Step 4: Create Invoice -----
                invoice = Invoice.objects.create(
                    invoice_number=invoice_number,
                    invoice_type=request.POST.get('invoice_type', 'invoice'),
                    status=request.POST.get('invoice_status', 'open'),
                    customer=customer,
                    owner=request.user,
                    issue_date=issue_date,
                    due_date=due_date,
                    discount=to_decimal(request.POST.get('invoice_discount', '0')),
                    shipping=to_decimal(request.POST.get('invoice_shipping', '0')),
                    notes=request.POST.get('invoice_notes', ''),
                    custom_email_message=request.POST.get('custom_email', ''),
                    subtotal=Decimal('0.00'),
                    total=Decimal('0.00'),
                    vat=Decimal('0.00'),
                )
                
                # ----- Step 5: Invoice Items -----
                products_list = request.POST.getlist('invoice_product[]')
                quantities = request.POST.getlist('invoice_product_qty[]')
                prices = request.POST.getlist('invoice_product_price[]')
                discounts = request.POST.getlist('invoice_product_discount[]')
                
                if not products_list or not any(products_list):
                    messages.error(request, 'At least one product is required!')
                    invoice.delete()
                    return redirect('invoices:invoice_create')
                
                subtotal = Decimal('0.00')
                
                for i in range(len(products_list)):
                    product_name = products_list[i].strip() if i < len(products_list) else ''
                    if not product_name:
                        continue
                    
                    qty = int(quantities[i]) if i < len(quantities) and quantities[i] else 1
                    price = to_decimal(prices[i]) if i < len(prices) else Decimal('0')
                    discount = discounts[i] if i < len(discounts) else ''
                    
                    item_subtotal = price * Decimal(str(qty))
                    
                    if discount:
                        discount_str = str(discount).strip()
                        try:
                            if '%' in discount_str:
                                percent = Decimal(discount_str.replace('%', '').strip())
                                discount_amount = item_subtotal * (percent / Decimal('100'))
                            else:
                                discount_amount = Decimal(discount_str)
                            item_subtotal = item_subtotal - discount_amount
                        except Exception:
                            pass
                    
                    InvoiceItem.objects.create(
                        invoice=invoice,
                        description=product_name,
                        quantity=qty,
                        price=price,
                        discount=discount if discount else '0',
                        subtotal=item_subtotal
                    )
                    
                    subtotal = subtotal + item_subtotal
                
                # ----- Step 6: Totals -----
                invoice.subtotal = subtotal
                invoice.discount = to_decimal(request.POST.get('invoice_discount', '0'))
                invoice.shipping = to_decimal(request.POST.get('invoice_shipping', '0'))
                
                total_before_vat = invoice.subtotal - invoice.discount + invoice.shipping
                
                if settings.ENABLE_VAT and settings.VAT_RATE > 0:
                    invoice.vat = total_before_vat * (Decimal(str(settings.VAT_RATE)) / Decimal('100'))
                    invoice.total = total_before_vat + invoice.vat
                else:
                    invoice.vat = Decimal('0.00')
                    invoice.total = total_before_vat
                
                invoice.save()
                
                messages.success(request, f'Invoice {invoice.invoice_number} created successfully!')
                return redirect('invoices:invoice_list')
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            messages.error(request, f'Error creating invoice: {str(e)}')
            return redirect('invoices:invoice_create')
    
    # ----- GET request -----
    # STRICT ISOLATION: Only calculate next invoice number for THIS user
    last_invoice = Invoice.objects.filter(owner=request.user).order_by('-id').first()
        
    if last_invoice:
        try:
            last_num = int(''.join(filter(str.isdigit, last_invoice.invoice_number)))
            next_num = last_num + 1
        except Exception:
            next_num = Invoice.objects.filter(owner=request.user).count() + 1
    else:
        next_num = 1
    
    next_invoice_number = f"{settings.INVOICE_PREFIX}{next_num:02d}"
    
    # STRICT ISOLATION: Only show THIS user's products and customers
    products_qs = Product.objects.filter(owner=request.user)
    customers_qs = Customer.objects.filter(owner=request.user)

    return render(request, 'invoices/invoice_create.html', {
        'next_invoice_number': next_invoice_number,
        'products': products_qs,
        'customers': customers_qs,
    })



# 3. INVOICE EDIT

@login_required
def invoice_edit(request, pk):
    # STRICT ISOLATION: Only allow editing if the user owns it
    invoice = get_object_or_404(Invoice, pk=pk, owner=request.user)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                invoice.invoice_type = request.POST.get('invoice_type', 'invoice')
                invoice.status = request.POST.get('invoice_status', 'open')
                invoice.issue_date = request.POST.get('invoice_date')
                invoice.due_date = request.POST.get('invoice_due_date')
                invoice.discount = to_decimal(request.POST.get('invoice_discount', '0'))
                invoice.shipping = to_decimal(request.POST.get('invoice_shipping', '0'))
                invoice.notes = request.POST.get('invoice_notes', '')
                invoice.custom_email_message = request.POST.get('custom_email', '')
                
                customer = invoice.customer
                customer.name = request.POST.get('customer_name', customer.name)
                customer.email = request.POST.get('customer_email', customer.email)
                customer.phone = request.POST.get('customer_phone', '')
                customer.address_line1 = request.POST.get('customer_address_1', '')
                customer.address_line2 = request.POST.get('customer_address_2', '')
                customer.city = request.POST.get('customer_town', '')
                customer.state = request.POST.get('customer_county', '')
                customer.postal_code = request.POST.get('customer_postcode', '')
                customer.save()
                
                invoice.items.all().delete()
                
                products_list = request.POST.getlist('invoice_product[]')
                quantities = request.POST.getlist('invoice_product_qty[]')
                prices = request.POST.getlist('invoice_product_price[]')
                discounts = request.POST.getlist('invoice_product_discount[]')
                
                subtotal = Decimal('0.00')
                for i in range(len(products_list)):
                    product_name = products_list[i].strip() if i < len(products_list) else ''
                    if not product_name:
                        continue
                    
                    qty = int(quantities[i]) if i < len(quantities) and quantities[i] else 1
                    price = to_decimal(prices[i]) if i < len(prices) else Decimal('0')
                    discount = discounts[i] if i < len(discounts) else ''
                    
                    item_subtotal = price * Decimal(str(qty))
                    
                    if discount:
                        discount_str = str(discount).strip()
                        try:
                            if '%' in discount_str:
                                percent = Decimal(discount_str.replace('%', '').strip())
                                discount_amount = item_subtotal * (percent / Decimal('100'))
                            else:
                                discount_amount = Decimal(discount_str)
                            item_subtotal = item_subtotal - discount_amount
                        except Exception:
                            pass
                    
                    InvoiceItem.objects.create(
                        invoice=invoice,
                        description=product_name,
                        quantity=qty,
                        price=price,
                        discount=discount if discount else '0',
                        subtotal=item_subtotal
                    )
                    subtotal = subtotal + item_subtotal
                
                invoice.subtotal = subtotal
                total_before_vat = subtotal - invoice.discount + invoice.shipping
                
                if settings.ENABLE_VAT and settings.VAT_RATE > 0:
                    invoice.vat = total_before_vat * (Decimal(str(settings.VAT_RATE)) / Decimal('100'))
                    invoice.total = total_before_vat + invoice.vat
                else:
                    invoice.vat = Decimal('0.00')
                    invoice.total = total_before_vat
                
                invoice.save()
                messages.success(request, f'Invoice {invoice.invoice_number} updated successfully!')
                return redirect('invoices:invoice_list')
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            messages.error(request, f'Error updating invoice: {str(e)}')
    
    # STRICT ISOLATION: Only show THIS user's products and customers
    products_qs = Product.objects.filter(owner=request.user)
    customers_qs = Customer.objects.filter(owner=request.user)

    return render(request, 'invoices/invoice_edit.html', {
        'invoice': invoice,
        'products': products_qs,
        'customers': customers_qs,
    })



# 4. INVOICE DELETE

@login_required
def invoice_delete(request, pk):
    # STRICT ISOLATION: Only allow deletion if the user owns it
    invoice = get_object_or_404(Invoice, pk=pk, owner=request.user)
    
    if request.method == 'POST':
        try:
            invoice_number = invoice.invoice_number
            invoice.delete()
            messages.success(request, f'Invoice {invoice_number} deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error deleting invoice: {str(e)}')
    
    return redirect('invoices:invoice_list')



# 5. INVOICE DOWNLOAD PDF

@login_required
def invoice_download_pdf(request, pk):
    # STRICT ISOLATION: Only allow downloading if the user owns it
    invoice = get_object_or_404(Invoice, pk=pk, owner=request.user)
        
    pdf_content = generate_invoice_pdf(invoice)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{invoice.invoice_number}.pdf"'
    response.write(pdf_content)
    return response



# 6. INVOICE EMAIL

@login_required
def invoice_email(request, pk):
    # STRICT ISOLATION: Only allow emailing if the user owns it
    invoice = get_object_or_404(Invoice, pk=pk, owner=request.user)
        
    messages.info(request, 'Email feature coming soon!')
    return redirect('invoices:invoice_list')