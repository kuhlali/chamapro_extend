from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from .models import Chama, Loan, Investment
from .forms import ChamaForm
from .forms_invite import InviteMemberForm
from .forms_loan import LoanRequestForm
from .forms_create import CreateChamaForm
from payments.models import MpesaTransaction
from .forms import InvestmentForm
from .forms_profile import EditProfileForm
from payments.utils import MpesaGateWay

User = get_user_model()

def home_view(request):
    """Home page view"""
    context = {
        'site_name': 'ChamaPro',
        'site_description': 'Professional Chama Management Platform with M-Pesa Integration',
        'site_keywords': 'chama management, investment group, M-Pesa integration, savings, loans, Kenya, Africa, fintech',
        'site_author': 'ChamaPro Team',
        'canonical_url': request.build_absolute_uri('/'),
        'og_type': 'website',
        'site_url': request.scheme + '://' + request.get_host(),
        'twitter_card': 'summary_large_image',
        'DEBUG': settings.DEBUG
    }
    return render(request, 'home.html', context)

def about_view(request):
    """About page view"""
    return render(request, 'about.html', {'title': 'About ChamaPro'})

def contact_view(request):
    """Contact page view"""
    return render(request, 'contact.html', {'title': 'Contact Us'})

def pricing_view(request):
    """View to display subscription plans"""
    return render(request, 'chama/pricing.html', {'title': 'Pricing Plans'})

@login_required
def dashboard_view(request):
    """User Dashboard showing their Chamas"""
    # Fetch all chamas the user is a member of (including ones they created)
    my_chamas = request.user.chamas.all()
    
    # Check if user has a valid M-Pesa number (starts with 254)
    # This helps users who might have signed up before strict validation or have invalid numbers
    user_phone = getattr(request.user, 'phone_number', '')
    if user_phone and not str(user_phone).startswith('254'):
         messages.warning(request, "Your registered phone number is not in the correct M-Pesa format (254...). Please update it in your profile to avoid payment errors.")

    context = {
        'title': 'Dashboard',
        'my_chamas': my_chamas,
    }
    return render(request, 'chama/dashboard.html', context)

@login_required
def chama_detail_view(request, slug, pk):
    """Detailed view of a specific Chama"""
    chama = get_object_or_404(Chama, id=pk, slug=slug)
    
    # Check if user is a member or the creator
    is_member = request.user == chama.created_by or request.user in chama.members.all()
    
    context = {'chama': chama, 'is_member': is_member}
    
    if is_member:
        # Calculate total collected (Real-time aggregation for accuracy)
        total_collected = MpesaTransaction.objects.filter(
            chama=chama,
            status='SUCCESS',
            transaction_type='CONTRIBUTION'
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        # Get all contributions for transparency
        contributions = MpesaTransaction.objects.filter(
            chama=chama,
            status='SUCCESS',
            transaction_type='CONTRIBUTION'
        ).select_related('user').order_by('-transaction_date')
        
        context.update({
            'total_collected': total_collected,
            'contributions': contributions
        })
    elif not chama.is_public:
        messages.error(request, "You must be a member to view this private group.")
        return redirect('chama:dashboard')
        
    return render(request, 'chama/chama_detail.html', context)

# Temporary placeholder views
def privacy_view(request):
    return HttpResponse("Privacy Policy - Coming Soon")

def terms_view(request):
    return HttpResponse("Terms of Service - Coming Soon")

def cookies_view(request):
    return HttpResponse("Cookie Policy - Coming Soon")

@login_required
def create_chama(request):
    """View to create a new Chama"""
    if request.method == 'POST':
        form = CreateChamaForm(request.POST, request.FILES)
        if form.is_valid():
            chama = form.save(commit=False)
            chama.created_by = request.user
            
            # Get plan from query parameter (default to BASIC)
            plan = request.GET.get('plan', 'BASIC').upper()
            chama.subscription_plan = plan
            
            chama.save()
            chama.members.add(request.user)
            
            # Redirect to payment if a paid plan is selected
            # TEMPORARY: Commented out to allow free creation for testing
            # if plan in ['STANDARD', 'PREMIUM']:
            #     return redirect('payments:pay_subscription', chama_id=chama.id)
                
            return redirect('chama:dashboard')
    else:
        form = CreateChamaForm()
    
    return render(request, 'chama/create_chama.html', {'form': form, 'title': 'Create New Chama'})

@login_required
def list_members(request, slug, pk):
    chama = get_object_or_404(Chama, id=pk, slug=slug)
    # Allow members and creator to view member list
    if request.user != chama.created_by and request.user not in chama.members.all():
        return redirect('chama:dashboard')
        
    return render(request, 'chama/members_list.html', {'chama': chama})

@login_required
def invite_member(request, slug, pk):
    chama = get_object_or_404(Chama, id=pk, slug=slug)
    
    # Only creator can invite (for now)
    if request.user != chama.created_by:
        return redirect('chama:chama_detail', slug=slug, pk=pk)

    if request.method == 'POST':
        form = InviteMemberForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user_to_add = User.objects.get(email=email)
            
            if user_to_add == chama.created_by:
                 form.add_error('email', 'You are already the owner of this Chama.')
            elif user_to_add in chama.members.all():
                form.add_error('email', 'User is already a member.')
            else:
                chama.members.add(user_to_add)
                return redirect('chama:members_list', slug=slug, pk=pk)
    else:
        form = InviteMemberForm()
    
    return render(request, 'chama/invite_member.html', {'form': form, 'chama': chama})

@login_required
def remove_member(request, slug, pk, member_id):
    """View to remove a member from a Chama"""
    chama = get_object_or_404(Chama, id=pk, slug=slug)
    
    # Authorization: Only the creator (admin) can remove members
    if request.user != chama.created_by:
        messages.error(request, "Access denied. Only the group admin can remove members.")
        return redirect('chama:members_list', slug=slug, pk=pk)

    member_to_remove = get_object_or_404(User, id=member_id)
    
    if member_to_remove == chama.created_by:
        messages.error(request, "You cannot remove yourself as the admin.")
    else:
        chama.members.remove(member_to_remove)
        messages.success(request, f"{member_to_remove.get_full_name() or member_to_remove.username} has been removed from the group.")
        
    return redirect('chama:members_list', slug=slug, pk=pk)

@login_required
def loan_list(request, slug, pk):
    """View to list loans and handle loan requests"""
    chama = get_object_or_404(Chama, id=pk, slug=slug)
    
    # Check membership
    if request.user != chama.created_by and request.user not in chama.members.all():
        return redirect('chama:dashboard')

    loans = chama.loans.all()
    
    if request.method == 'POST':
        form = LoanRequestForm(request.POST)
        if form.is_valid():
            loan = form.save(commit=False)
            loan.chama = chama
            loan.borrower = request.user
            loan.save()
            messages.success(request, "Loan request submitted successfully.")
            return redirect('chama:loan_list', slug=slug, pk=pk)
    else:
        form = LoanRequestForm()

    return render(request, 'chama/loan_list.html', {
        'chama': chama,
        'loans': loans,
        'form': form
    })

@login_required
def approve_loan(request, slug, pk, loan_id):
    """Admin action to approve a loan"""
    chama = get_object_or_404(Chama, id=pk, slug=slug)
    loan = get_object_or_404(Loan, id=loan_id, chama=chama)
    
    if request.user != chama.created_by:
        messages.error(request, "Only the admin can approve loans.")
    else:
        # Check if Chama has enough balance
        if chama.total_balance < loan.amount:
            messages.error(request, f"Insufficient Chama balance (KES {chama.total_balance}) to disburse KES {loan.amount}.")
            return redirect('chama:loan_list', slug=slug, pk=pk)

        # Initiate B2C Payment
        gateway = MpesaGateWay()
        # Ensure phone number is in 254 format
        phone = loan.borrower.phone_number
        if phone and phone.startswith('0'):
            phone = '254' + phone[1:]
            
        response = gateway.disburse_funds(phone, loan.amount, remarks=f"Loan for {loan.borrower.username}")
        
        if response.get('ResponseCode') == '0':
            loan.status = 'DISBURSED' # Update status to disbursed immediately for now
            loan.action_by = request.user
            loan.action_date = timezone.now()
            loan.save()
            
            # Deduct from Chama Balance
            chama.total_balance -= loan.amount
            chama.save()
            
            messages.success(request, f"Loan approved and KES {loan.amount} sent to {loan.borrower.first_name}.")
        else:
            # FALLBACK FOR TESTING: Allow approval even if M-Pesa fails (e.g. invalid B2C creds)
            loan.status = 'DISBURSED'
            loan.action_by = request.user
            loan.action_date = timezone.now()
            loan.save()
            
            # Deduct from Chama Balance locally
            chama.total_balance -= loan.amount
            chama.save()
            
            messages.warning(request, f"Loan marked DISBURSED (Test Mode). M-Pesa API Error: {response.get('ResponseDescription')}")
        
    return redirect('chama:loan_list', slug=slug, pk=pk)

@login_required
def reject_loan(request, slug, pk, loan_id):
    """Admin action to reject a loan"""
    chama = get_object_or_404(Chama, id=pk, slug=slug)
    loan = get_object_or_404(Loan, id=loan_id, chama=chama)
    
    if request.user != chama.created_by:
        messages.error(request, "Only the admin can reject loans.")
    else:
        loan.status = 'REJECTED'
        loan.action_by = request.user
        loan.action_date = timezone.now()
        loan.save()
        messages.warning(request, "Loan request rejected.")
        
    return redirect('chama:loan_list', slug=slug, pk=pk)

@login_required
def profile_view(request):
    """User Profile and Settings View"""
    user = request.user
    
    # Calculate total contributions across all chamas
    total_contributed = MpesaTransaction.objects.filter(
        user=user, 
        status='SUCCESS', 
        transaction_type='CONTRIBUTION'
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    # Get recent transactions
    recent_transactions = MpesaTransaction.objects.filter(user=user).order_by('-transaction_date')[:5]

    context = {
        'title': 'Profile & Settings',
        'user': user,
        'total_contributed': total_contributed,
        'recent_transactions': recent_transactions,
        'chamas_count': user.chamas.count(),
    }
    return render(request, 'account/profile.html', context)

@login_required
def edit_profile(request):
    """View to edit user profile"""
    if request.method == 'POST':
        form = EditProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully.')
            return redirect('chama:profile')
    else:
        form = EditProfileForm(instance=request.user)
    
    return render(request, 'account/edit_profile.html', {'form': form, 'title': 'Edit Profile'})

@login_required
def change_password(request):
    """View to change user password"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important! to keep user logged in
            messages.success(request, 'Your password was successfully updated!')
            return redirect('chama:profile')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'account/change_password.html', {'form': form, 'title': 'Change Password'})

@login_required
def reports_view(request):
    """View for financial reports and contribution trends"""
    user = request.user
    
    # Calculate monthly contribution trend
    trend_data = MpesaTransaction.objects.filter(
        user=user,
        status='SUCCESS',
        transaction_type='CONTRIBUTION'
    ).annotate(
        month=TruncMonth('transaction_date')
    ).values('month').annotate(
        total=Sum('amount')
    ).order_by('month')
    
    months = [entry['month'].strftime('%B %Y') for entry in trend_data if entry['month']]
    amounts = [float(entry['total']) for entry in trend_data if entry['month']]

    context = {
        'title': 'Reports',
        'trend_months': months,
        'trend_amounts': amounts,
    }
    return render(request, 'reports.html', context)

def features_view(request):
    context = {'title': 'Features'}
    return render(request, 'features.html', context)

def investment_list(request, slug, pk):
    chama = get_object_or_404(Chama, slug=slug, pk=pk)
    investments = chama.investments.all().order_by('-date_invested')
    return render(request, 'chama/investment_list.html', {'chama': chama, 'investments': investments})

def add_investment(request, slug, pk):
    chama = get_object_or_404(Chama, slug=slug, pk=pk)
    if request.method == 'POST':
        form = InvestmentForm(request.POST)
        if form.is_valid():
            investment = form.save(commit=False)
            investment.chama = chama
            investment.save()
            messages.success(request, 'Investment added successfully!')
            return redirect('chama:investment_list', slug=slug, pk=pk)
    else:
        form = InvestmentForm()
    return render(request, 'chama/investment_form.html', {'chama': chama, 'form': form, 'action': 'Add'})

def edit_investment(request, slug, pk, investment_id):
    chama = get_object_or_404(Chama, slug=slug, pk=pk)
    investment = get_object_or_404(Investment, id=investment_id, chama=chama)
    if request.method == 'POST':
        form = InvestmentForm(request.POST, instance=investment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Investment updated successfully!')
            return redirect('chama:investment_list', slug=slug, pk=pk)
    else:
        form = InvestmentForm(instance=investment)
    return render(request, 'chama/investment_form.html', {'chama': chama, 'form': form, 'action': 'Edit'})

def delete_investment(request, slug, pk, investment_id):
    chama = get_object_or_404(Chama, slug=slug, pk=pk)
    investment = get_object_or_404(Investment, id=investment_id, chama=chama)
    if request.method == 'POST':
        investment.delete()
        messages.success(request, 'Investment deleted successfully!')
    return redirect('chama:investment_list', slug=slug, pk=pk)
