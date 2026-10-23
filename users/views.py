from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.contrib.auth.hashers import make_password


# Helper to check if user is Admin
def is_admin(user):
    return user.is_superuser



# 1. USER SIGN UP (Public)

def signup(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')
        
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        # Validation
        if not email or not password:
            messages.error(request, 'Email and Password are required.')
            return redirect('signup')

        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return redirect('signup')

        if User.objects.filter(username=email).exists():
            messages.error(request, 'An account with this email already exists.')
            return redirect('signup')

        try:
            #  CHANGED: is_active=True and auto-approved so they can log in immediately
            user = User.objects.create(
                username=email,
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=make_password(password),
                is_active=True 
            )
            
            # Save phone and set auto-approved in profile
            user.profile.phone = phone
            user.profile.is_approved = True 
            user.profile.save()

            messages.success(request, 'Account created successfully! You can now log in.')
            return redirect('login')
        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
            return redirect('signup')

    return render(request, 'users/signup.html')



# 2. USER LIST (Admin Only)

@login_required
@user_passes_test(is_admin, login_url='core:dashboard')
def user_list(request):
    #  Only admins can view this page
    users = User.objects.all().order_by('-date_joined')
    paginator = Paginator(users, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'users/user_list.html', {'page_obj': page_obj})



# 3. USER APPROVE (Admin Only)

@login_required
@user_passes_test(is_admin, login_url='core:dashboard')
def user_approve(request, pk):
    user = get_object_or_404(User, pk=pk)
    
    # Prevent admin from accidentally deactivating themselves
    if user == request.user:
        messages.error(request, 'You cannot change your own approval status.')
        return redirect('users:user_list')

    user.is_active = True
    user.profile.is_approved = True
    user.save()
    
    messages.success(request, f'User "{user.email}" has been approved and can now log in.')
    return redirect('users:user_list')



# 4. USER DELETE (Admin Only)

@login_required
@user_passes_test(is_admin, login_url='core:dashboard')
def user_delete(request, pk):
    if request.method == 'POST':
        user = get_object_or_404(User, pk=pk)
        
        # Prevent self-deletion
        if user == request.user:
            messages.error(request, 'You cannot delete your own admin account!')
            return redirect('users:user_list')

        try:
            email = user.email
            user.delete()
            messages.success(request, f'User "{email}" deleted successfully.')
        except Exception as e:
            messages.error(request, f'Error deleting user: {str(e)}')
            
    return redirect('users:user_list')

