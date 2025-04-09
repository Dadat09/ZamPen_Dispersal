from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q, F
from django.contrib import messages
from .models import Grower, User, Farmer
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .forms import GrowerForm, UserForm, FarmerForm, SimpleGrowerForm, FarmerForm2, FarmGrowerForm
import uuid
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils.text import slugify
from django.http import JsonResponse

def ViewGrowers(request):
    if request.user.is_staff:
        layout = 'admin.html'
    else:
        layout = 'base.html'
    
    query = request.GET.get('q', '')
    sort_by = request.GET.get('sort_by', 'id')
    direction = request.GET.get('direction', 'asc')

    growers = Grower.objects.select_related('linked_user')
    
    if query:
        growers = growers.filter(
            Q(linked_user__username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(ContactNo__icontains=query) |
            Q(Email__icontains=query) |
            Q(barangay__icontains=query) |
            Q(city__icontains=query) |
            Q(province__icontains=query)
        )

    if direction == 'reset':
        sort_by = 'id'
        direction = 'asc'

    if direction == 'asc':
        growers = growers.order_by(F(sort_by).asc())
    else:
        growers = growers.order_by(F(sort_by).desc())

    paginator = Paginator(growers, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'title': "View Growers",
        'page_obj': page_obj,
        'sort_by': sort_by,
        'direction': direction,
        'layout': layout
    }

    return render(request, 'viewgrowers.html', context)


def AddGrowers(request):
    layout = 'admin.html' if request.user.is_staff else 'base.html'

    try:
        if request.method == 'POST':
            grower_form = GrowerForm(request.POST)  # Removed request=request
            user_form = UserForm(request.POST, request.FILES)

            if grower_form.is_valid():
                user_choice = grower_form.cleaned_data.get('user_choice')

                if user_choice == 'other':
                    if user_form.is_valid():
                        user = user_form.save(commit=False)
                        user.username = user_form.cleaned_data['user_name']
                        user.set_password(user_form.cleaned_data['password'])
                        user.is_grower = True
                        user.save()

                        grower = grower_form.save(commit=False)
                        grower.linked_user = user
                        grower.created_by = request.user  # Automate setting created_by
                        grower.save()

                        messages.success(request, 'Grower and new user created successfully!')
                        return redirect('grower')

                elif user_choice == 'existing':
                    existing_user_id = request.POST.get('existing_user')
                    if existing_user_id:
                        existing_user = User.objects.get(id=existing_user_id)
                        existing_user.is_grower = True
                        existing_user.save()

                        grower = grower_form.save(commit=False)
                        grower.linked_user = existing_user
                        grower.created_by = request.user  # Automate setting created_by
                        grower.save()

                        messages.success(request, 'Grower linked to existing user!')
                        return redirect('grower')

                else:
                    grower = grower_form.save(commit=False)
                    grower.linked_user = None
                    grower.created_by = request.user  # Automate setting created_by
                    grower.save()

                    messages.success(request, 'Grower created without linking a user.')
                    return redirect('grower')

    except Exception as e:
        print("An error occurred:", str(e))

    grower_form = GrowerForm()  # Removed request=request
    user_form = UserForm()

    return render(request, 'addgrowers.html', {
        'grower_form': grower_form,
        'user_form': user_form,
        'layout': layout
    })

def editGrower(request, pk):
    grower = get_object_or_404(Grower, pk=pk)
    layout = 'admin.html' if request.user.is_staff else 'base.html'

    if request.method == 'POST':
        grower_form = GrowerForm(request.POST, instance=grower)
        user_choice = request.POST.get('user_choice')

        if grower_form.is_valid():
            grower = grower_form.save(commit=False)
            grower.first_name = grower_form.cleaned_data.get('new_user_first_name', grower.first_name)
            grower.last_name = grower_form.cleaned_data.get('new_user_last_name', grower.last_name)
            grower.ContactNo = grower_form.cleaned_data['ContactNo']
            grower.Email = grower_form.cleaned_data['Email']
            grower.barangay = grower_form.cleaned_data['barangay']
            grower.city = grower_form.cleaned_data['city']
            grower.province = grower_form.cleaned_data['province']
            grower.zipcode = grower_form.cleaned_data['zipcode']
            grower.notes = grower_form.cleaned_data['notes']
            
            if user_choice == 'other':
                user_form = UserForm(request.POST, request.FILES)
                if user_form.is_valid():
                    user = user_form.save(commit=False)
                    user.username = user_form.cleaned_data['user_name']
                    user.set_password(user_form.cleaned_data['password'])
                    user.save()
                    grower.linked_user = user
            elif user_choice == 'existing':
                existing_user_id = request.POST.get('existing_user')
                if existing_user_id:
                    grower.linked_user = User.objects.get(id=existing_user_id)
            else:
                grower.linked_user = None

            grower.save()
            messages.success(request, 'Grower updated successfully!')
            return redirect('grower')

    else:
        # Determine the correct initial user choice
        initial_user_choice = 'none'
        if grower.linked_user:
            initial_user_choice = 'existing'

        # Populate the form with the initial user choice
        grower_form = GrowerForm(instance=grower, initial={'user_choice': initial_user_choice, 'existing_user': grower.linked_user})

    return render(request, 'editgrowers.html', {
        'grower_form': grower_form,
        'layout': layout
    })


def deleteGrower(request, pk):
    if request.user.is_staff:
        layout = 'admin.html'
    else:
        layout = 'base.html'

    grower = get_object_or_404(Grower, pk=pk)
    if request.method == "POST":
        grower.delete()
        return redirect('grower')
    return redirect('grower')

def userView(request):
    if request.user.is_staff:
        layout = 'admin.html'
    else:
        layout = 'base.html'

    query = request.GET.get('q', '')
    filter_option = request.GET.get('filter', '')

    # Base queryset for users
    users = User.objects.all()

    # Enhanced filtering
    if filter_option == 'growers':
        users = users.filter(is_grower=True)
    elif filter_option == 'farmers':
        users = users.filter(is_farmer=True)
    
    users = users.filter(
        Q(username__icontains=query) |
        Q(first_name__icontains=query) |
        Q(middle_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(email__icontains=query)
    )

    paginator = Paginator(users, 10)  # Show 10 users per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'viewusers.html', {
        'users': page_obj,
        'query': query,
        'layout': layout,
        'filter': filter_option,  # Pass the filter option to the template
    })


def AddUser(request):
    layout = 'admin.html' if request.user.is_staff else 'base.html'

    if request.method == 'POST':
        user_form = UserForm(request.POST, request.FILES)
        user_type = request.POST.get('user_type')
        grower_form = SimpleGrowerForm(request.POST) if user_type == 'grower' else SimpleGrowerForm()
        farmer_form = FarmerForm(request.POST) if user_type == 'farmer' else FarmerForm()

        if user_form.is_valid():
            user_instance = user_form.save(commit=False)

            # Generate unique username if not provided
            if not user_instance.username:
                base_username = slugify(user_instance.first_name + user_instance.last_name)
                counter = 1
                while User.objects.filter(username=base_username).exists():
                    base_username = f"{slugify(user_instance.first_name + user_instance.last_name)}{counter}"
                    counter += 1
                user_instance.username = base_username

            # Validate and encrypt password
            password = request.POST.get('password')
            try:
                validate_password(password, user_instance)
                user_instance.set_password(password)
            except ValidationError as e:
                messages.error(request, f"Password error: {', '.join(e.messages)}")
                return render(request, 'adduser.html', {
                    'user_form': user_form,
                    'grower_form': grower_form,
                    'farmer_form': farmer_form,
                    'layout': layout,
                })

            # Set user type
            user_instance.is_grower = user_type == 'grower'
            user_instance.is_farmer = user_type == 'farmer'
            user_instance.save()

            # Retrieve contact number
            contact_no = request.POST.get('contact_number', '')

            # Handle Grower creation
            if user_type == 'grower' and grower_form.is_valid():
                grower = grower_form.save(commit=False)
                grower.linked_user = user_instance
                grower.first_name = user_instance.first_name
                grower.last_name = user_instance.last_name
                grower.ContactNo = contact_no
                grower.Email = user_instance.email
                grower.created_by = request.user
                grower.save()
                messages.success(request, 'Grower added successfully!')
            elif user_type == 'grower':
                messages.error(request, 'Grower form is invalid.')

            # Handle Farmer creation
            if user_type == 'farmer' and farmer_form.is_valid():
                farmer = farmer_form.save(commit=False)
                farmer.Name = user_instance
                farmer.ContactNo = contact_no
                farmer.Email = user_instance.email
                farmer.created_by = request.user
                farmer.save()
                messages.success(request, 'Farmer added successfully!')
            elif user_type == 'farmer':
                messages.error(request, 'Farmer form is invalid.')

            return redirect('user')
        else:
            messages.error(request, 'User form is invalid.')

    else:
        user_form = UserForm()
        grower_form = SimpleGrowerForm()
        farmer_form = FarmerForm()

    return render(request, 'adduser.html', {
        'user_form': user_form,
        'grower_form': grower_form,
        'farmer_form': farmer_form,
        'layout': layout,
    })



def EditUser(request, pk):
    user_instance = get_object_or_404(User, pk=pk)
    layout = 'admin.html' if request.user.is_staff else 'base.html'

    # Get existing grower or farmer instance
    grower_instance = Grower.objects.filter(linked_user=user_instance).first()
    farmer_instance = Farmer.objects.filter(Name=user_instance).first()
    
    # Determine current user type
    user_type = 'grower' if grower_instance else 'farmer' if farmer_instance else None

    if request.method == 'POST':
        user_form = UserForm(request.POST, request.FILES, instance=user_instance)
        user_type = request.POST.get('user_type')

        # Select appropriate form based on user type
        grower_form = SimpleGrowerForm(request.POST, instance=grower_instance) if user_type == 'grower' else None
        farmer_form = FarmerForm(request.POST, instance=farmer_instance) if user_type == 'farmer' else None

        if user_form.is_valid():
            user_instance = user_form.save(commit=False)
            user_instance.is_grower = user_type == 'grower'
            user_instance.is_farmer = user_type == 'farmer'
            user_instance.save()

            if user_type == 'grower':
                # Create or update Grower instance
                if grower_form and grower_form.is_valid():
                    grower = grower_form.save(commit=False)
                    grower.linked_user = user_instance
                    grower.first_name = user_instance.first_name
                    grower.last_name = user_instance.last_name
                    grower.Email = user_instance.email
                    grower.save()
                
                # Remove Farmer instance if switching from farmer to grower
                if farmer_instance:
                    farmer_instance.delete()

                messages.success(request, 'Grower updated successfully!')

            elif user_type == 'farmer':
                # Create or update Farmer instance
                if farmer_form and farmer_form.is_valid():
                    farmer = farmer_form.save(commit=False)
                    farmer.Name = user_instance
                    farmer.Email = user_instance.email
                    farmer.save()

                # Remove Grower instance if switching from grower to farmer
                if grower_instance:
                    grower_instance.delete()

                messages.success(request, 'Farmer updated successfully!')

            return redirect('user')

    else:
        user_form = UserForm(instance=user_instance)
        grower_form = SimpleGrowerForm(instance=grower_instance) if grower_instance else SimpleGrowerForm()
        farmer_form = FarmerForm(instance=farmer_instance) if farmer_instance else FarmerForm()

    return render(request, 'editusers.html', {
        'user_form': user_form,
        'grower_form': grower_form,
        'farmer_form': farmer_form,
        'user_instance': user_instance,
        'user_type': user_type,
        'layout': layout,
    })


def Deleteuser(request, id):
    user = get_object_or_404(User, id=id)
    if request.method == 'POST':
        user.delete()
        messages.success(request, 'User deleted successfully.')
        return redirect('user')  # Redirect back to the user list view.
    return redirect('user')

def ViewFarmers(request):
    if request.user.is_staff:
        layout = 'admin.html'
    else:
        layout = 'base.html'

    query = request.GET.get('q', '')
    sort_by = request.GET.get('sort_by', 'id')
    direction = request.GET.get('direction', 'asc')

    farmers = Farmer.objects.select_related('Name')

    if query:
        farmers = farmers.filter(
            Q(Name__username__icontains=query) |
            Q(Name__first_name__icontains=query) |
            Q(Name__last_name__icontains=query) |
            Q(ContactNo__icontains=query) |
            Q(Email__icontains(query))
        )

    if direction == 'reset':
        sort_by = 'id'
        direction = 'asc'

    if direction == 'asc':
        farmers = farmers.order_by(F(sort_by).asc())
    else:
        farmers = farmers.order_by(F(sort_by).desc())

    paginator = Paginator(farmers, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'title': "View Farmers",
        'page_obj': page_obj,
        'sort_by': sort_by,
        'direction': direction,
        'layout': layout
    }

    return render(request, 'viewfarmers.html', context)

# views.py

def AddFarmer(request):
    layout = 'admin.html' if request.user.is_staff else 'base.html'

    try:
        user_instance = None  # ✅ Ensure user_instance is initialized

        if request.method == 'POST':
            farmer_form = FarmerForm2(request.POST)

            # Check if the user is updating an existing user
            user_choice = request.POST.get('user_choice')
            if user_choice == 'existing':
                existing_user_id = request.POST.get('existing_user')
                user_instance = User.objects.get(id=existing_user_id) if existing_user_id else None
            else:
                user_instance = User()

            existing_password = user_instance.password if user_instance else None
            user_form = UserForm(request.POST, request.FILES, instance=user_instance)

            if user_form.is_valid():
                user_instance = user_form.save(commit=False)
                if not request.POST.get('password') and existing_password:
                    user_instance.password = existing_password  # Retain old password
                user_instance.is_grower = request.POST.get('user_type') == 'grower'
                user_instance.is_farmer = request.POST.get('user_type') == 'farmer'
                user_instance.save()

            if farmer_form.is_valid():
                user_choice = farmer_form.cleaned_data.get('user_choice')

                if user_choice == 'other' and user_form.is_valid():
                    user = user_form.save(commit=False)
                    user.username = user_form.cleaned_data['user_name']
                    user.set_password(user_form.cleaned_data['password'])
                    user.save()

                    farmer = farmer_form.save(commit=False)
                    farmer.Name = user
                    farmer.created_by = request.user  # Assign the current user to created_by
                    farmer.save()

                    messages.success(request, 'Farmer and new user created successfully!')
                    return redirect('farmer')

                elif user_choice == 'existing':
                    existing_user_id = farmer_form.cleaned_data.get('existing_user')
                    if existing_user_id:
                        farmer = farmer_form.save(commit=False)
                        farmer.Name = existing_user_id
                        farmer.created_by = request.user
                        farmer.save()

                        messages.success(request, 'Farmer linked to existing user!')
                        return redirect('farmer')

                else:
                    farmer = farmer_form.save(commit=False)
                    farmer.Name = None
                    farmer.created_by = request.user
                    farmer.save()

                    messages.success(request, 'Farmer created without linking a user.')
                    return redirect('farmer')

    except Exception as e:
        print("An error occurred:", str(e))

    farmer_form = FarmerForm2()
    user_form = UserForm()

    return render(request, 'addfarmers.html', {
        'farmer_form': farmer_form,
        'user_form': user_form,
        'layout': layout
    })

def Deletefarmer(request, pk):
    if request.user.is_staff:
        layout = 'admin.html'
    else:
        layout = 'base.html'

    farmer = get_object_or_404(Farmer, pk=pk)
    if request.method == "POST":
        farmer.delete()
        return redirect('farmer')
    return redirect('farmer')

def custom_login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            if user.is_staff:
                return redirect('dashboard')  # Redirect to dashboard for staff users
            else:
                return redirect('index')  # Redirect to homepage for non-staff users
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('index')

def save_farm_grower(request):
    if request.method == "POST":
        form = FarmGrowerForm(request.POST)
        if form.is_valid():
            grower = form.save(commit=False)  # ✅ Create instance before assigning attributes

            # Assign correct field names
            grower.first_name = form.cleaned_data['new_user_first_name']
            grower.last_name = form.cleaned_data['new_user_last_name']
            grower.Email = form.cleaned_data['new_user_email']

            if request.user.is_authenticated:
                grower.created_by = request.user  # Assign the currently logged-in user

            grower.save()

            # ✅ Return JSON response for AJAX requests
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    "success": True,
                    "message": "Grower saved successfully!",
                    "grower": {"id": grower.id, "name": f"{grower.first_name} {grower.last_name}"}
                })

            messages.success(request, "Grower information saved successfully!")

        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({"success": False, "errors": form.errors})

            messages.error(request, "There was an error saving the form. Please check the inputs.")

        return redirect(request.META.get('HTTP_REFERER', 'default_redirect_url'))  # Redirect for non-AJAX requests

    return JsonResponse({"success": False, "error": "Invalid request method"}, status=400)