from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q, F
from django import forms
from auth_user.models import Grower
from .models import Grower, User
from .forms import GrowerForm, UserForm
from django.contrib import messages

def ViewGrowers(request):
    # Get search query and filter values from the request
    query = request.GET.get('q', '')
    
    # Get sorting parameters, defaulting to 'id' (pk) and 'asc'
    sort_by = request.GET.get('sort_by', 'id')
    direction = request.GET.get('direction', 'asc')

    # Fetch all growers
    growers = Grower.objects.select_related('Name')  # Use select_related to optimize related User model fetching

    # Filter the queryset based on the search query
    if query:
        growers = growers.filter(
            Q(Name__username__icontains=query) |
            Q(Name__first_name__icontains=query) |  # Filter by first name
            Q(Name__last_name__icontains=query) |   # Filter by last name
            Q(ContactNo__icontains=query) |
            Q(Email__icontains=query) |
            Q(barangay__icontains=query) |
            Q(city__icontains=query) |
            Q(province__icontains=query)
        )

    # Reset sorting if direction is "reset"
    if direction == 'reset':
        sort_by = 'id'  # Default sorting field
        direction = 'asc'  # Reset to ascending order

    # Apply sorting
    if direction == 'asc':
        growers = growers.order_by(F(sort_by).asc())
    else:
        growers = growers.order_by(F(sort_by).desc())

    # Set up pagination
    paginator = Paginator(growers, 10)  # Show 10 entries per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Context passed to the template
    context = {
        'title': "View Growers",
        'page_obj': page_obj,
        'sort_by': sort_by,  # Pass current sorting state to the template
        'direction': direction  # Pass current sorting direction to the template
    }

    return render(request, 'viewgrowers.html', context)

def AddGrowers(request):
    try:
        if request.method == 'POST':
            grower_form = GrowerForm(request.POST, request=request)
            user_form = UserForm(request.POST, request.FILES)

            if grower_form.is_valid():
                user_choice = grower_form.cleaned_data.get('user_choice')

                # If "Other" is selected, create a new user
                if user_choice == 'other':
                    if user_form.is_valid():
                        user = user_form.save(commit=False)
                        user.username = user_form.cleaned_data['user_name']  # Set email as the username
                        user.set_password(user_form.cleaned_data['password'])  # Set the password from the form
                        user.save()

                        grower = grower_form.save(commit=False)
                        grower.Name = user
                        grower.save()

                        messages.success(request, 'Grower and new user created successfully!')
                        return redirect('grower')

                # If "Existing" is selected, link the selected user
                elif user_choice == 'existing':
                    existing_user_id = request.POST.get('existing_user')
                    if existing_user_id:
                        existing_user = User.objects.get(id=existing_user_id)
                        grower = grower_form.save(commit=False)
                        grower.Name = existing_user
                        grower.save()

                        messages.success(request, 'Grower linked to existing user!')
                        return redirect('grower')

                # If "None" is selected
                else:
                    grower = grower_form.save(commit=False)
                    grower.Name = None
                    grower.save()

                    messages.success(request, 'Grower created without linking a user.')
                    return redirect('grower')

    except Exception as e:
        print("An error occurred:", str(e))

    else:
        grower_form = GrowerForm(request=request)
        user_form = UserForm()

    return render(request, 'addgrowers.html', {
        'grower_form': grower_form,
        'user_form': user_form,
    })

def editGrower(request, pk):
    grower = get_object_or_404(Grower, pk=pk)  # Fetch the grower object by its primary key (pk)

    if request.method == 'POST':
        grower_form = GrowerForm(request.POST, request=request, instance=grower)
        user_form = UserForm(request.POST, request.FILES)

        if grower_form.is_valid():
            user_choice = grower_form.cleaned_data.get('user_choice')

            # If "Other" is selected, update or create a new user
            if user_choice == 'other':
                if user_form.is_valid():
                    user = user_form.save(commit=False)
                    user.username = user_form.cleaned_data['user_name']
                    user.set_password(user_form.cleaned_data['password'])
                    user.save()

                    grower = grower_form.save(commit=False)
                    grower.Name = user
                    grower.save()

                    messages.success(request, 'Grower and new user updated successfully!')
                    return redirect('grower')

            # If "Existing" is selected, link the selected user
            elif user_choice == 'existing':
                existing_user_id = request.POST.get('existing_user')
                if existing_user_id:
                    existing_user = User.objects.get(id=existing_user_id)
                    grower.Name = existing_user
                    grower.save()

                    messages.success(request, 'Grower linked to existing user!')
                    return redirect('grower')

            # If "None" is selected
            else:
                grower.Name = None
                grower.save()

                messages.success(request, 'Grower updated without linking a user.')
                return redirect('grower')

    else:
        grower_form = GrowerForm(instance=grower, request=request)
        user_form = UserForm()

    return render(request, 'editgrowers.html', {
        'grower_form': grower_form,
        'user_form': user_form,
    })

def deleteGrower(request, pk):
    grower = get_object_or_404(Grower, pk=pk)
    if request.method == "POST":
        grower.delete()
        return redirect('grower')  # Redirect to the grower listing page
    return redirect('grower')