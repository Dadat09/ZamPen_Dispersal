from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView
from .models import *
from django.http import JsonResponse
from auth_user.models import Grower
from .forms import LivestockForm, LivestockFamilyForm, FarmLocationForm, DispersalForm, MessageForm
from django.core.paginator import Paginator
from django.db.models import Count, Q, F, Prefetch
from django.contrib import messages
from django.urls import reverse
from datetime import timedelta,  datetime
import csv
from django.http import HttpResponse
from .models import FarmLocation, Livestock
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from django.contrib.auth.decorators import login_required
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
    if request.user.is_authenticated:
        if request.user.is_staff:
            Livestocks = Livestock.objects.all()
        else:
            Livestocks = Livestock.objects.filter(
                livestock_family__dispersal__grower__Name=request.user
            )
    else:
        # Handle unauthenticated users gracefully
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
    if request.method == 'POST':
        form = LivestockForm(request.POST)
        if form.is_valid():
            livestock = form.save(commit=False)
            tag_color = request.POST.get('custom_tag_color') or form.cleaned_data['tag_color']
            livestock.tag_color = tag_color
            livestock.date_recorded = timezone.now()
            livestock.save()
            return redirect('livestock')
    else:
        form = LivestockForm()

    return render(request, 'addchicken.html', {'form': form})

from django.utils import timezone

def addLivestockFamily(request):
    if request.method == 'POST':
        form = LivestockFamilyForm(request.POST)
        if form.is_valid():
            # Save the LivestockFamily instance
            livestock_family = form.save(commit=True)

            # Set date_recorded to the current date
            livestock_family.date_recorded = timezone.now().date()
            livestock_family.save()  # Save again to update the date_recorded

            return redirect('family')  # Redirect to family list or success page
        else:
            print(form.errors)  # Print errors to help debug

    else:
        form = LivestockFamilyForm()

    return render(request, 'addfamily.html', {'form': form})

def addFarmLocation(request):
    if request.method == 'POST':
        form = FarmLocationForm(request.POST)
        if form.is_valid():
            # Save the form, which includes latitude and longitude
            form.save()
            return redirect('farm')  # Change to your actual success URL
    else:
        form = FarmLocationForm()

    # Fetch the growers to populate the dropdown    
    grower_list = Grower.objects.all()
    return render(request, 'addfarmlocation.html', {'form': form, 'grower_list': grower_list})

def addDispersal(request):
    if request.method == "POST":
        form = DispersalForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('dispersal')  # Replace with the correct URL for the dispersal list page
    else:
        form = DispersalForm()
    
    context = {
        'form': form,
        'title': "Add Dispersal"
    }
    return render(request, 'adddispersal.html', context)

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
    livestock = get_object_or_404(Livestock, pk=pk)

    if request.method == 'POST':
        form = LivestockForm(request.POST, instance=livestock)
        if form.is_valid():
            form.save()
            return redirect('livestock')  # Redirect to a livestock list page
    else:
        form = LivestockForm(instance=livestock)

    return render(request, 'editchicken.html', {'form': form, 'livestock': livestock})

def editLivestockFamily(request, pk):
    livestock_family = get_object_or_404(LivestockFamily, pk=pk)

    if request.method == 'POST':
        form = LivestockFamilyForm(request.POST, instance=livestock_family)
        if form.is_valid():
            # Update the LivestockFamily instance
            livestock_family = form.save(commit=False)

            # Automatically update the date_recorded field to the current date
            livestock_family.date_recorded = timezone.now().date()
            livestock_family.save()  # Save changes

            return redirect('family')  # Redirect to the family list or detail page
        else:
            print(form.errors)  # Print errors to help debug

    else:
        form = LivestockFamilyForm(instance=livestock_family)

    return render(request, 'editfamily.html', {'form': form, 'livestock_family': livestock_family})

def editFarmLocation(request, pk):
    farm_location = get_object_or_404(FarmLocation, pk=pk)

    if request.method == 'POST':
        form = FarmLocationForm(request.POST, instance=farm_location)
        if form.is_valid():
            # Save the updated FarmLocation instance
            form.save()
            return redirect('farm')  # Redirect to the farm list page after saving
    else:
        form = FarmLocationForm(instance=farm_location)

    return render(request, 'editfarmlocation.html', {'form': form, 'farm_location': farm_location})

def editDispersal(request, pk):
    dispersal = get_object_or_404(Dispersal, pk=pk)  # Get the specific dispersal record
    
    if request.method == "POST":
        form = DispersalForm(request.POST, instance=dispersal)  # Pass the dispersal instance
        if form.is_valid():
            form.save()
            return redirect('dispersal')  # Redirect to the appropriate list or detail page
    else:
        form = DispersalForm(instance=dispersal)  # Pass the instance when editing
    
    context = {
        'form': form,
        'title': "Edit Dispersal"
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


from datetime import timedelta, datetime

def dashboardView(request):
    # Count families not dispersed
    families_not_dispersed_count = LivestockFamily.objects.annotate(
        dispersal_count=Count('dispersal')
    ).filter(dispersal_count=0).count()

    # Count dispersed families
    dispersed_families_count = Dispersal.objects.count()

    # Count male and female livestock
    male_count = Livestock.objects.filter(gender='Male').count()
    female_count = Livestock.objects.filter(gender='Female').count()

    # Calculate total livestock count
    total_livestock_count = male_count + female_count

    # Count total farms
    total_farms_count = FarmLocation.objects.count()

    # Query to count chickens added per day
    chickens_added_per_day = (
        Livestock.objects
        .values('date_recorded')
        .annotate(count=Count('id'))
        .order_by('date_recorded')
    )

    # Prepare data for the chart
    weeks = []
    chickens_added = []

    for entry in chickens_added_per_day:
        weeks.append(entry['date_recorded'])
        chickens_added.append(entry['count'])

    # Check if there are any records
    if weeks:
        # Fill missing dates with zero counts
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

    # Convert dates to strings for the frontend chart
    weeks = [date.strftime('%Y-%m-%d') for date in weeks]

    # Get all farms with their owners and addresses, and related dispersals and families dispersed
    farms = FarmLocation.objects.prefetch_related(
        'dispersal_set__families_dispersed'
    ).select_related('grower').all()

    # Prepare the context for the template
    context = {
        'families_not_dispersed': families_not_dispersed_count,
        'dispersed_families': dispersed_families_count,
        'male_count': male_count,
        'female_count': female_count,
        'total_livestock_count': total_livestock_count,
        'total_farms_count': total_farms_count,
        'farms': farms,
        'weeks': weeks,  # Pass the formatted date strings to the template
        'chickens_added': chickens_added,  # Pass chicken counts to the template
        'title': "Dashboard"
    }

    return render(request, 'dashboard.html', context)




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