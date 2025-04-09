from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView
from .models import *
from .models import SystemSettings
from django.http import FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from auth_user.models import Grower, Farmer
import os
from .forms import LivestockForm, LivestockFamilyForm, FarmLocationForm, DispersalForm, MessageForm
from auth_user.forms import FarmGrowerForm
from django.core.paginator import Paginator
from django.db.models import Count, Q, F, Prefetch
from django.contrib import messages
from django.urls import reverse
from datetime import timedelta,  datetime
from django.utils import timezone
import csv
from django.utils.timezone import now,  make_aware
from django.http import HttpResponse
from .models import FarmLocation, Livestock
from reportlab.lib.pagesizes import A4, letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from django.utils.timezone import localtime
from reportlab.pdfgen import canvas
from collections import defaultdict
from django.contrib.auth.decorators import login_required
from .forms import SystemSettingsForm
import tempfile

def indexView(request):
    title = 'Zampen Chicken Dispersal'
    context = {
        'title':title
    }
    return render(request, 'index.html', context)


def AboutView(request):
    title = 'About'
    context = {
        'title':title
    }
    return render(request, 'aboutus.html', context)

def ContactView(request):
    title = 'Contact Us'
    
    # Initialize form with default values if the user is logged in
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            # Save the message to the database
            form.save()
            # Show a success message
            messages.success(request, 'Your message has been sent successfully!')
            # Redirect to the same page after successful form submission
            return redirect('contact')
    else:
        # Pre-fill form with user data if logged in
        if request.user.is_authenticated:
            # Create a new form instance with pre-filled data
            form = MessageForm(initial={
                'name': f"{request.user.first_name} {request.user.last_name}" if request.user.first_name and request.user.last_name else None,
                'email': request.user.email
            })
        else:
            form = MessageForm()

    context = {
        'title': title,
        'form': form,
    }
    return render(request, 'contact.html', context)

@login_required
def ViewChickens(request):
    # Determine layout based on user role
    layout = 'admin.html' if request.user.is_staff else 'base.html'

    # Retrieve search query and filters
    query = request.GET.get('q', '')
    tag_color_filter = request.GET.get('tag_color', '')

    # Get sorting parameters, defaulting to 'ls_code' and ascending order
    sort_by = request.GET.get('sort_by', 'ls_code')
    direction = request.GET.get('direction', 'asc')

    # Fetch livestock based on user permissions
    if request.user.is_superuser:
        Livestocks = Livestock.objects.all()
    elif request.user.is_authenticated and request.user.is_grower:
        Livestocks = Livestock.objects.filter(
            livestock_family__in=LivestockFamily.objects.filter(grower=request.user)
        )
    elif request.user.is_authenticated and request.user.is_farmer:
        try:
            farmer = Farmer.objects.get(Name=request.user)
            Livestocks = Livestock.objects.filter(
                livestock_family__in=LivestockFamily.objects.filter(grower=farmer.created_by)
            )
        except Farmer.DoesNotExist:
            Livestocks = Livestock.objects.none()
    else:
        # Handle unauthenticated users or users without grower/farmer role gracefully
        Livestocks = Livestock.objects.none()

    # Update the age of each livestock
    for entry in Livestocks:
        entry.update_age()

    # Apply search filter
    if query:
        Livestocks = Livestocks.filter(
            Q(ls_code__icontains=query) |
            Q(gender__icontains=query) |
            Q(batch_no__icontains=query) |
            Q(tag_color__icontains=query)
        )

    # Apply tag color filter
    if tag_color_filter:
        Livestocks = Livestocks.filter(tag_color=tag_color_filter)

    # Reset sorting if direction is "reset"
    if direction == 'reset':
        sort_by = 'ls_code'
        direction = 'asc'

    # Apply sorting based on the chosen field and direction
    try:
        if direction == 'asc':
            Livestocks = Livestocks.order_by(F(sort_by).asc())
        else:
            Livestocks = Livestocks.order_by(F(sort_by).desc())
    except FieldError:
        # Handle invalid field names gracefully
        sort_by = 'ls_code'  # Reset to default sort field
        direction = 'asc'
        Livestocks = Livestocks.order_by(F(sort_by).asc())

    # Retrieve unique tag colors for the filter dropdown
    unique_tag_colors = Livestock.objects.values_list('tag_color', flat=True).distinct()

    # Paginate the results
    paginator = Paginator(Livestocks, 10)  # Show 10 entries per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Context passed to the template
    context = {
        'title': "View Chicken",
        'page_obj': page_obj,
        'unique_tag_colors': unique_tag_colors,
        'sort_by': sort_by,  # Current sorting field
        'direction': direction,  # Current sorting direction
        'layout': layout,
    }

    return render(request, 'viewchickens.html', context)

@login_required
def ViewFamilies(request):
    layout = 'admin.html' if request.user.is_staff else 'base.html'
    query = request.GET.get('q')

    if request.user.is_staff:
        families = LivestockFamily.objects.annotate(
            hen_count=Count('livestock', filter=Q(livestock__gender='Female')),  # Count hens
            rooster_count=Count('livestock', filter=Q(livestock__gender='Male'))  # Count roosters
        )
    elif request.user.is_authenticated:
        families = LivestockFamily.objects.filter(
            dispersal__grower__Name=request.user
        ).annotate(
            hen_count=Count('livestock', filter=Q(livestock__gender='Female')),  # Count hens
            rooster_count=Count('livestock', filter=Q(livestock__gender='Male'))  # Count roosters
        )
    else:
        # If no user is logged in, return an empty queryset
        families = LivestockFamily.objects.none()

    if query:
        families = families.filter(
            Q(family_id__icontains=query) |
            Q(brood_generation_number__icontains=query) |
            Q(batch_no__icontains=query)
        )

    paginator = Paginator(families, 10)  # Show 10 programs per page.
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'title': "View Families",
        'page_obj': page_obj,
        'layout': layout,
    }

    return render(request, 'viewfamilies.html', context)

def ViewFarms(request):
    layout = 'admin.html' if request.user.is_staff else 'base.html'
    query = request.GET.get('q')
    farms = FarmLocation.objects.all()
    
    sort_by = request.GET.get('sort_by', 'name')  # Default sort by name
    direction = request.GET.get('direction', 'asc')  # Default sort direction is ascending
    
    # Apply filtering based on search query
    if query:
        farms = farms.filter(
            Q(name__icontains=query) |
            Q(address__icontains=query)
        )
    
    # Sorting logic
    if direction == 'asc':
        farms = farms.order_by(F(sort_by).asc(nulls_last=True))
    elif direction == 'desc':
        farms = farms.order_by(F(sort_by).desc(nulls_last=True))

    # Pagination
    paginator = Paginator(farms, 10)  # Show 10 farms per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'title': "View Farms",
        'page_obj': page_obj,
        'sort_by': sort_by,
        'direction': direction,
        'layout': layout,
    }

    return render(request, 'viewfarms.html', context)


@login_required
def ViewDispersals(request):
    layout = 'admin.html' if request.user.is_staff else 'base.html'
    query = request.GET.get('q', '')

    if request.user.is_staff:
        dispersals = Dispersal.objects.all()  # Staff can view all dispersals
    else:
        dispersals = Dispersal.objects.filter(grower__Name=request.user)  # Filter by logged-in user

    sort_by = request.GET.get('sort_by', 'dispersal_date')  # Default sort by dispersal_date
    direction = request.GET.get('direction', 'asc')  # Default sort direction is ascending

    # Apply filtering based on search query (can search grower name or farm location)
    if query:
        dispersals = dispersals.filter(
            Q(grower__Name__first_name__icontains=query) | 
            Q(grower__Name__last_name__icontains=query) |
            Q(grower__Name__username__icontains=query) |  
            Q(farmlocation__name__icontains=query)
        )

    # Sorting logic
    if direction == 'asc':
        dispersals = dispersals.order_by(F(sort_by).asc(nulls_last=True))
    elif direction == 'desc':
        dispersals = dispersals.order_by(F(sort_by).desc(nulls_last=True))

    # Pagination
    paginator = Paginator(dispersals, 10)  # Show 10 dispersals per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'title': "View Dispersals",
        'page_obj': page_obj,
        'sort_by': sort_by,
        'direction': direction,
        'query': query,
        'layout': layout,
    }

    return render(request, 'viewdispersals.html', context)

def addChickens(request):
    layout = 'admin.html' if request.user.is_staff else 'base.html'
    tag_colors = Livestock.objects.values_list('tag_color', flat=True).distinct()

    if request.method == 'POST':
        form = LivestockForm(request.POST, request.FILES)

        if form.is_valid():
            livestock = form.save(commit=False)

            if livestock:  # Ensure livestock is not None
                livestock.tag_color = request.POST.get('custom_tag_color') or form.cleaned_data['tag_color']
                livestock.date_recorded = timezone.now()

                # Save profile picture if provided
                if 'profile_picture' in request.FILES:
                    livestock.profile_picture = request.FILES['profile_picture']

                # Check if a new family should be created
                if 'create_family' in request.POST:
                    family_id = request.POST.get('family_id')
                    cage_location = request.POST.get('cage_location')
                    brood_generation_number = request.POST.get('brood_generation_number', 1)

                    if family_id and cage_location:
                        new_family, created = LivestockFamily.objects.get_or_create(
                            family_id=family_id,
                            defaults={
                                'cage_location': cage_location,
                                'date_recorded': timezone.now(),
                                'brood_generation_number': int(brood_generation_number)
                            }
                        )
                        livestock.livestock_family = new_family

                livestock.save()
                return redirect('livestock')
        else:
            print(f"Form Errors: {form.errors}")  # Debugging line

    else:
        form = LivestockForm()

    return render(request, 'addchicken.html', {'form': form,'layout': layout, 'tag_colors': tag_colors})

def addLivestockFamily(request):
    tag_colors = Livestock.objects.values_list('tag_color', flat=True).distinct()

    if request.method == 'POST':
        form = LivestockFamilyForm(request.POST, request=request)  # Pass request
        chicken_form = LivestockForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            return redirect('family')

    else:
        form = LivestockFamilyForm(request=request)  # Pass request
        chicken_form = LivestockForm()

    return render(request, 'addfamily.html', {
        'form': form,
        'chicken_form': chicken_form,
        'tag_colors': tag_colors,
    })


def addFarmLocation(request):
    layout = 'admin.html' if request.user.is_staff else 'base.html'
    if request.method == 'POST':
        farmform = FarmGrowerForm(request.POST)
        form = FarmLocationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('farm')  # Change to your actual success URL
    else:
        form = FarmLocationForm()
        farmform = FarmGrowerForm()  # Initialize farmform for GET requests

    # Fetch the growers to populate the dropdown    
    grower_list = Grower.objects.all()
    return render(request, 'addfarmlocation.html', {'layout' : layout, 'form': form, 'farmform': farmform, 'grower_list': grower_list})

def addDispersal(request):
    layout = 'admin.html' if request.user.is_staff else 'base.html'
    if request.method == "POST":
        form = DispersalForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Dispersal added successfully!")
            return redirect('dispersal')
    else:
        form = DispersalForm()

    # Fetch Growers and Farms for Dropdowns
    grower_list = Grower.objects.all()
    farm_list = FarmLocation.objects.all()

    # Initialize Farm Location Form for Modal
    farmform = FarmLocationForm()

    return render(request, 'adddispersal.html', {
        'form': form,
        'grower_list': grower_list,
        'farm_list': farm_list,
        'farmform': farmform,
        'layout' : layout,
        'title' : "Add Dispersal"
    })

def fetch_farms(request):
    grower_id = request.GET.get('grower_id')

    # Handle the case where grower_id is not provided or invalid
    if not grower_id:
        return JsonResponse({'error': 'Grower ID not provided'}, status=400)

    try:
        # Retrieve farms for the given grower
        farms = FarmLocation.objects.filter(grower_id=grower_id).values('id', 'name')
        return JsonResponse({'farms': list(farms)})
    except Exception as e:
        # Log the error and return a friendly JSON error message
        return JsonResponse({'error': str(e)}, status=500)

def editLivestock(request, pk):
    layout = 'admin.html' if request.user.is_staff else 'base.html'
    livestock = get_object_or_404(Livestock, pk=pk)

    if request.method == 'POST':
        form = LivestockForm(request.POST, request.FILES, instance=livestock)  # Include request.FILES

        if form.is_valid():
            # If a new image is uploaded, it replaces the old one
            if 'profile_picture' in request.FILES:
                livestock.profile_picture = request.FILES['profile_picture']

            form.save()
            return redirect('livestock')  # Redirect after saving

    else:
        form = LivestockForm(instance=livestock)

    return render(request, 'editchicken.html', {'form': form, 'layout':layout, 'livestock': livestock})

def editLivestockFamily(request, pk):
    livestock_family = get_object_or_404(LivestockFamily, pk=pk)
    tag_colors = Livestock.objects.values_list('tag_color', flat=True).distinct()

    if request.method == 'POST':
        form = LivestockFamilyForm(request.POST, instance=livestock_family, request=request)
        chicken_form = LivestockForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            messages.success(request, "Family updated successfully!")
            return redirect('family')  # Redirect to the family list instead of reloading edit

    else:
        form = LivestockFamilyForm(instance=livestock_family, request=request)
        chicken_form = LivestockForm()

    return render(request, 'editfamily.html', {
        'form': form,
        'chicken_form': chicken_form,
        'tag_colors': tag_colors,
        'livestock_family': livestock_family
    })

def editFarmLocation(request, pk):
    layout = 'admin.html' if request.user.is_staff else 'base.html'
    farm_location = get_object_or_404(FarmLocation, pk=pk)

    if request.method == 'POST':
        form = FarmLocationForm(request.POST, instance=farm_location)
        if form.is_valid():
            form.save()
            messages.success(request, "Farm location updated successfully!")
            return redirect('farm')  # Redirect to the farm list page
    else:
        form = FarmLocationForm(instance=farm_location)

    # Fetch all growers for the dropdown
    grower_list = Grower.objects.all()
    
    # Initialize the grower form for the "Add Grower" modal
    farmform = FarmGrowerForm()

    return render(request, 'editfarmlocation.html', {
        'form': form, 
        'farm_location': farm_location, 
        'grower_list': grower_list,
        'farmform': farmform,  # Pass grower form to template
        'layout' : layout
    })

def editDispersal(request, pk):
    layout = 'admin.html' if request.user.is_staff else 'base.html'
    dispersal = get_object_or_404(Dispersal, pk=pk)  # Get the specific dispersal record
    
    if request.method == "POST":
        form = DispersalForm(request.POST, instance=dispersal)  # Pass the dispersal instance
        if form.is_valid():
            form.save()
            return redirect('dispersal')  # Redirect to the appropriate list or detail page
    else:
        form = DispersalForm(instance=dispersal)  # Pass the instance when editing

    # Fetch Growers and Farms for Dropdowns
    grower_list = Grower.objects.all()
    farm_list = FarmLocation.objects.all()

    # Initialize Farm Location Form for Modal
    farmform = FarmLocationForm()

    context = {
        'form': form,
        'title': "Edit Dispersal",
        'grower_list': grower_list,
        'farm_list': farm_list,
        'farmform': farmform,
        'layout' : layout
    }
    return render(request, 'editdispersal.html', context)


def deleteLivestock(request, pk):
    # Fetch the livestock entry by primary key
    livestock = get_object_or_404(Livestock, pk=pk)
    
    if request.method == 'POST':
        # Delete the livestock entry
        livestock.delete()
        messages.success(request, "Livestock entry deleted successfully.")
        return redirect(reverse('livestock'))  # Redirect back to the listing page

    return redirect(reverse('livestock'))  # Redirect in case of a GET request

def deleteFamily(request, pk):
    family = get_object_or_404(LivestockFamily, pk=pk)
    if request.method == 'POST':
        family.delete()
        messages.success(request, 'Family entry deleted successfully.')
        return redirect('family')
    return render(request, 'delete_family.html', {'family': family})

def deleteFarm(request, pk):
    farm = get_object_or_404(FarmLocation, pk=pk)
    if request.method == "POST":
        farm.delete()
        return redirect('farm')  # Redirect to the farm listing page
    return redirect('farm')

def deleteDispersal(request, pk):
    dispersal = get_object_or_404(Dispersal, pk=pk)
    if request.method == "POST":
        dispersal.delete()
        messages.success(request, 'Dispersal deleted successfully!')
        return redirect('dispersal')
    return render(request, 'dispersal_confirm_delete.html', {'dispersal': dispersal})

@login_required
def dashboardView(request):
    tag_colors = Livestock.objects.values_list('tag_color', flat=True).distinct()
    livestock_form = LivestockForm()
    family_form = LivestockFamilyForm()
    total_growers = Grower.objects.count()
    year = request.GET.get('year', None) or str(now().year)
    grower_id = request.GET.get('grower_id', 'all')

    # Base livestock query (without filtering by grower yet)
    livestock = Livestock.objects.filter(date_recorded__year=year)

    dispersals = Dispersal.objects.filter(dispersal_date__year=year)

    # **Correct Grower Filtering**
    if grower_id != "all":
        try:
            grower_id = int(grower_id)  # Convert grower_id to integer
            relevant_families = LivestockFamily.objects.filter(
                dispersal__in=Dispersal.objects.filter(
                    farmlocation__grower_id=grower_id
        )
        ).values_list("family_id", flat=True)  # ✅ Use "family_id"

            # Filter livestock by families connected to the selected grower
            livestock = livestock.filter(livestock_family_id__in=relevant_families)

        except ValueError:
            return JsonResponse({'error': 'Invalid grower_id'}, status=400)

    # **Count Dispersed vs. Not Dispersed Families**
    families_not_dispersed_count = LivestockFamily.objects.filter(dispersal=None).count()
    dispersed_families_count = LivestockFamily.objects.filter(dispersal__isnull=False).distinct().count()   

    # **Livestock Gender Breakdown**
    male_count = livestock.filter(gender='Male').count()
    female_count = livestock.filter(gender='Female').count()
    total_livestock_count = male_count + female_count
    total_farms_count = FarmLocation.objects.count()

    # **Age Distribution**
    age_distribution = defaultdict(int)
    for animal in livestock:
        age = animal.age_in_days
        if age <= 30:
            age_distribution["0-30 days"] += 1
        elif age <= 60:
            age_distribution["31-60 days"] += 1
        elif age <= 90:
            age_distribution["61-90 days"] += 1
        else:
            age_distribution["90+ days"] += 1

    # **Chickens Added Per Day**
    chickens_added_per_day = (
        livestock
        .values('date_recorded')
        .annotate(count=Count('id'))
        .order_by('date_recorded')
    )

    dates = [entry["date_recorded"].strftime('%Y-%m-%d') for entry in chickens_added_per_day]
    chickens_added = [entry["count"] for entry in chickens_added_per_day]

    growers = Grower.objects.all()

    # **Return JSON if AJAX Request**
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'total_growers': total_growers,
            'families_not_dispersed': families_not_dispersed_count,
            'dispersed_families': dispersed_families_count,
            'male_count': male_count,
            'female_count': female_count,
            'total_livestock_count': total_livestock_count,
            'total_farms_count': total_farms_count,
            'age_labels': list(age_distribution.keys()),
            'age_counts': list(age_distribution.values()),
            'dates': dates,
            'chickens_added': chickens_added,
        })

    # **Context for Django Template Rendering**
    context = {
        "livestock_form": livestock_form,
        "family_form": family_form,
        'total_growers': total_growers,
        'families_not_dispersed': families_not_dispersed_count,
        'dispersed_families': dispersed_families_count,
        'male_count': male_count,
        'female_count': female_count,
        'total_livestock_count': total_livestock_count,
        'total_farms_count': total_farms_count,
        'age_labels': list(age_distribution.keys()),
        'age_counts': list(age_distribution.values()),
        'growers': growers,
        'available_years': list(range(now().year - 5, now().year + 1)),
        'title': "Dashboard",
        'tag_colors' : tag_colors
    }

    return render(request, "dashboard.html", context)


def farm_list(request):
    farms = FarmLocation.objects.prefetch_related('dispersal_set__families_dispersed').all()
    
    # Pagination
    paginator = Paginator(farms, 5)  # Show 5 farms per page
    page_number = request.GET.get('page')
    farm_page = paginator.get_page(page_number)
    
    context = {
        'farms': farm_page,
    }
    return render(request, 'your_template.html', context)

def exportfarmscsv(request):
    # Define HTTP response with CSV content type
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="farms_list.csv"'

    # Create a CSV writer
    writer = csv.writer(response)
    writer.writerow(['Farm Name', 'Owner', 'Address', 'Dispersed Families'])

    # Fetch farm data
    farms = FarmLocation.objects.prefetch_related('dispersal_set__families_dispersed').select_related('grower').all()

    for farm in farms:
        dispersed_families = ", ".join([str(family) for dispersal in farm.dispersal_set.all() for family in dispersal.families_dispersed.all()])
        writer.writerow([farm.name, farm.grower.Name, farm.address, dispersed_families])

    return response

def downloadfarmspdf(request):
    # Create HTTP response with PDF content type
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="farms.pdf"'

    # Set up PDF canvas
    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    # Title
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, height - 100, "Farms List")

    # Headers
    p.setFont("Helvetica-Bold", 12)
    headers = ['Farm Name', 'Owner', 'Address', 'Dispersed Families']
    x_offset = 100
    y_offset = height - 140
    for header in headers:
        p.drawString(x_offset, y_offset, header)
        x_offset += 150
    y_offset -= 20

    # Data rows
    farms = FarmLocation.objects.select_related('grower').prefetch_related('dispersal_set__families_dispersed').all()
    p.setFont("Helvetica", 10)
    for farm in farms:
        x_offset = 100
        dispersed_families = ', '.join([str(family) for dispersal in farm.dispersal_set.all() for family in dispersal.families_dispersed.all()])
        farm_data = [farm.name, farm.grower.Name, farm.address, dispersed_families]
        
        for data in farm_data:
            p.drawString(x_offset, y_offset, str(data))
            x_offset += 150
        y_offset -= 20
        # Create a new page if needed
        if y_offset < 50:
            p.showPage()
            y_offset = height - 50

    p.showPage()
    p.save()
    return response

def ContactView(request):
    if request.method == 'POST':
        form = MessageForm(request.POST)
        
        if form.is_valid():
            message_instance = form.save(commit=False)
            if request.user.is_authenticated:
                message_instance.name = request.user.get_full_name()
                message_instance.email = request.user.email
                message_instance.user = request.user
            message_instance.save()
            messages.success(request, 'Your message has been sent successfully!')
            return redirect('contact')

    else:
        # Prefill the form if the user is logged in
        initial_data = {}
        if request.user.is_authenticated:
            initial_data = {'name': request.user.get_full_name(), 'email': request.user.email}
        form = MessageForm(initial=initial_data)
    
    return render(request, 'contact.html', {'form': form, 'title': 'Contact Us'})

def MessagesView(request):
    layout = 'admin.html' if request.user.is_staff else 'base.html'
    query = request.GET.get('q', '')
    message_type_filter = request.GET.get('message_type', '')

    # Get sorting parameters
    sort_by = request.GET.get('sort_by', 'created_at')
    direction = request.GET.get('direction', 'asc')

    # Fetch all messages and apply filters
    messages = Message.objects.all()
    if query:
        messages = messages.filter(
            Q(message__icontains=query) |  # Filter by message content
            Q(name__icontains=query)  # Filter by sender name
        )

    if message_type_filter:
        messages = messages.filter(message_type=message_type_filter)

    # Reset sorting if direction is "reset"
    if direction == 'reset':
        sort_by = 'created_at'
        direction = 'asc'

    # Apply sorting
    if direction == 'asc':
        messages = messages.order_by(F(sort_by).asc())
    else:
        messages = messages.order_by(F(sort_by).desc())

    # Get unique message types for filtering
    unique_message_types = Message.objects.values_list('message_type', flat=True).distinct()

    # Set up pagination
    paginator = Paginator(messages, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'title': "View Messages",
        'page_obj': page_obj,
        'unique_message_types': unique_message_types,
        'sort_by': sort_by,
        'direction': direction,
        'layout': layout,
    }

    return render(request, 'viewmessages.html', context)

def user_dashboard_view(request):
    user = request.user

    # Filter data based on the specific user
    farms = FarmLocation.objects.filter(grower__Name=user).prefetch_related(
        'dispersal_set__families_dispersed'
    ).select_related('grower')

    families_not_dispersed_count = LivestockFamily.objects.filter(
        grower__Name=user
    ).annotate(
        dispersal_count=Count('dispersal')
    ).filter(dispersal_count=0).count()

    dispersed_families_count = Dispersal.objects.filter(
        grower__Name=user
    ).count()

    male_count = Livestock.objects.filter(gender='Male', livestock_family__grower__Name=user).count()
    female_count = Livestock.objects.filter(gender='Female', livestock_family__grower__Name=user).count()

    total_livestock_count = male_count + female_count

    total_farms_count = farms.count()

    chickens_added_per_day = (
        Livestock.objects.filter(livestock_family__grower__Name=user)
        .values('date_recorded')
        .annotate(count=Count('id'))
        .order_by('date_recorded')
    )

    weeks = []
    chickens_added = []

    for entry in chickens_added_per_day:
        weeks.append(entry['date_recorded'])
        chickens_added.append(entry['count'])

    if weeks:
        start_date = weeks[0]
        end_date = weeks[-1]
        all_dates = []

        current_date = start_date
        while current_date <= end_date:
            all_dates.append(current_date)
            current_date += timedelta(days=1)

        chickens_added_full = []
        week_set = set(weeks)
        for date in all_dates:
            if date in week_set:
                chickens_added_full.append(chickens_added[weeks.index(date)])
            else:
                chickens_added_full.append(0)

        weeks = all_dates
        chickens_added = chickens_added_full

    weeks = [date.strftime('%Y-%m-%d') for date in weeks]

    context = {
        'families_not_dispersed': families_not_dispersed_count,
        'dispersed_families': dispersed_families_count,
        'male_count': male_count,
        'female_count': female_count,
        'total_livestock_count': total_livestock_count,
        'total_farms_count': total_farms_count,
        'farms': farms,
        'weeks': weeks,
        'chickens_added': chickens_added,
        'title': "User Dashboard",
    }

    return render(request, 'user_dashboard.html', context)

def addChicken(request):
    tag_colors = Livestock.objects.values_list('tag_color', flat=True).distinct()

    if request.method == 'POST':
        form = LivestockForm(request.POST, request.FILES)

        if form.is_valid():
            new_chicken = form.save(commit=False)
            new_chicken.date_recorded = timezone.now()

            # Ensure tag color is set correctly
            if new_chicken.tag_color == 'other' and form.cleaned_data.get('custom_tag_color'):
                new_chicken.tag_color = form.cleaned_data['custom_tag_color']

            new_chicken.save()
            messages.success(request, "Chicken added successfully!")

            return redirect(request.META.get('HTTP_REFERER', 'addfamily'))  # Retain form data

        else:
            messages.error(request, f"Failed to add chicken: {form.errors}")

    return redirect(request.META.get('HTTP_REFERER', 'addfamily'))

def save_farm_location(request):
    if request.method == "POST":
        form = FarmLocationForm(request.POST)
        if form.is_valid():
            farm = form.save()
            return JsonResponse({"success": True, "farm": {"id": farm.id, "name": farm.name}})
        else:
            return JsonResponse({"success": False, "errors": form.errors})
    return JsonResponse({"success": False, "message": "Invalid request."})

@csrf_exempt
def update_settings(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            settings = SystemSettings.get_settings()
            settings.max_roosters = int(data["max_roosters"])
            settings.max_hens = int(data["max_hens"])
            settings.save()

            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request"})

@login_required
def settingsView(request):
    settings = SystemSettings.get_settings()

    if request.method == "POST":
        form = SystemSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            form.save()
            messages.success(request, "Settings updated successfully!")
            return redirect('dashboard')  # Redirect to dashboard
    else:
        form = SystemSettingsForm(instance=settings)

    return render(request, "settings.html", {"form": form})
@csrf_exempt

def update_settings(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            settings = SystemSettings.get_settings()
            settings.max_roosters = int(data["max_roosters"])
            settings.max_hens = int(data["max_hens"])
            settings.save()

            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request"})

def get_settings(request):
    settings = SystemSettings.get_settings()
    return JsonResponse({
        "success": True,
        "max_roosters": settings.max_roosters,
        "max_hens": settings.max_hens
    })
 
@csrf_exempt    
def add_chicken(request):
    if request.method == "POST":
        form = LivestockForm(request.POST, request.FILES)
        if form.is_valid():
            new_chicken = form.save(commit=False)

            # Handle custom tag color
            if new_chicken.tag_color == "other" and "custom_tag_color" in request.POST:
                new_chicken.tag_color = request.POST["custom_tag_color"]

            new_chicken.save()
            return JsonResponse({"success": True})  # ✅ Always return valid JSON
        
        return JsonResponse({"success": False, "error": form.errors.as_json()}, status=400)
    
    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)

@csrf_exempt
def add_family(request):
    if request.method == "POST":
        form = LivestockFamilyForm(request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({"success": True})  # ✅ Always return JSON
        
        return JsonResponse({"success": False, "error": form.errors.as_json()}, status=400)
    
    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)


def family_detail_view(request, family_id):
    family = get_object_or_404(LivestockFamily, pk=family_id)

    # Check if family is dispersed
    dispersal = Dispersal.objects.filter(families_dispersed=family).first()
    is_dispersed = dispersal is not None

    # Get farm location and grower if dispersed
    farm_location = dispersal.farmlocation if is_dispersed else None
    grower = farm_location.grower if is_dispersed else None

    # Get all chickens in this family
    roosters = Livestock.objects.filter(livestock_family=family, gender="Male")
    hens = Livestock.objects.filter(livestock_family=family, gender="Female")

    context = {
        "family": family,
        "is_dispersed": is_dispersed,
        "farm_location": farm_location,
        "grower": grower,
        "roosters": roosters,
        "hens": hens,
    }

    return render(request, "familydetail.html", context)

def generate_family_pdf(file_path):
    # Query Livestock Families
    families = LivestockFamily.objects.all()
    
    data = [["Family Name", "Location", "Grower", "Dispersed", "Dispersal Date", "Livestocks"]]
    
    for family in families:
        dispersal = Dispersal.objects.filter(families_dispersed=family).first()
        location = dispersal.farmlocation.name if dispersal else "N/A"
        grower = dispersal.farmlocation.grower if dispersal else "N/A"
        dispersed = "Yes" if dispersal else "No"
        dispersal_date = (
                            localtime(make_aware(datetime.combine(dispersal.dispersal_date, datetime.min.time()))).strftime('%Y-%m-%d') 
                            if dispersal and dispersal.dispersal_date 
                            else "N/A"
                        )
        livestock_list = ", ".join(Livestock.objects.filter(livestock_family=family).values_list("ls_code", flat=True))
        
        data.append([family.family_id, location, str(grower), dispersed, dispersal_date, livestock_list])
    
    # Create PDF
    doc = SimpleDocTemplate(file_path, pagesize=letter)
    table = Table(data)
    
    # Style Table
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ])
    table.setStyle(style)
    
    doc.build([table])
    return file_path

def download_family_pdf(request):
    # Use a safer temporary directory
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, f"livestock_families_{now().strftime('%Y%m%d%H%M%S')}.pdf")

    # Ensure the directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Generate the PDF
    generate_family_pdf(file_path)

    # Serve the PDF
    return FileResponse(open(file_path, 'rb'), content_type='application/pdf', as_attachment=True, filename="livestock_families.pdf")