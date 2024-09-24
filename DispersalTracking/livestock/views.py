from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from .models import *
from auth_user.models import Grower
from .forms import LivestockForm, LivestockFamilyForm, FarmLocationForm
from django.core.paginator import Paginator
from django.db.models import Count, Q, F

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
    context = {
        'title':title
    }
    return render(request, 'contact.html', context)

def ViewChickens(request):
    # Get search query and filter values from the request
    query = request.GET.get('q', '')
    tag_color_filter = request.GET.get('tag_color', '')

    # Get sorting parameters, defaulting to 'ls_code' (ID) and 'asc'
    sort_by = request.GET.get('sort_by', 'ls_code')
    direction = request.GET.get('direction', 'asc')

    # Fetch all livestock and update age for each entry
    Livestocks = Livestock.objects.all()
    for entry in Livestocks:
        entry.update_age()

    # Filter the queryset based on the search query and tag color filter
    if query:
        Livestocks = Livestocks.filter(
            Q(ls_code__icontains=query) |
            Q(gender__icontains=query) |
            Q(batch_no__icontains=query) |
            Q(tag_color__icontains=query)
        )

    if tag_color_filter:
        Livestocks = Livestocks.filter(tag_color=tag_color_filter)

    # Reset sorting if direction is "reset"
    if direction == 'reset':
        sort_by = 'ls_code'  # Default sorting field
        direction = 'asc'  # Reset to ascending order

    # Apply sorting
    if direction == 'asc':
        Livestocks = Livestocks.order_by(F(sort_by).asc())
    else:
        Livestocks = Livestocks.order_by(F(sort_by).desc())

    # Get unique tag colors for the filter dropdown
    unique_tag_colors = Livestock.objects.values_list('tag_color', flat=True).distinct()

    # Set up pagination
    paginator = Paginator(Livestocks, 10)  # Show 10 entries per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Context passed to the template
    context = {
        'title': "View Chicken",
        'page_obj': page_obj,
        'unique_tag_colors': unique_tag_colors,
        'sort_by': sort_by,  # Pass current sorting state to the template
        'direction': direction  # Pass current sorting direction to the template
    }

    return render(request, 'viewchickens.html', context)

def ViewFamilies(request):
    query = request.GET.get('q')
    families = LivestockFamily.objects.annotate(
        hen_count=Count('livestock', filter=Q(livestock__gender='Female')),  # Count hens
        rooster_count=Count('livestock', filter=Q(livestock__gender='Male'))  # Count roosters
    )
    if query:
        families = families.filter( 
            Q(family_id__icontains=query) |
            Q(brood_generation_number__icontains=query)|
            Q(batch_no__icontains=query)
        )

    paginator = Paginator(families, 10)  # Show 10 programs per page.
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
         'title' : "View Families",
        'page_obj': page_obj,
          }

    return render(request, 'viewfamilies.html', context)

from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q, F
from .models import FarmLocation

def ViewFarms(request):
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
    }

    return render(request, 'viewfarms.html', context)

def ViewDispersals(request):
    query = request.GET.get('q')
    dispersals = Dispersal.objects.all()
    if query:
        dispersals = dispersals.filter( 
            Q(grower__icontains=query) |
            Q(farmlocation__icontains=query)
        )

    paginator = Paginator(dispersals, 10)  # Show 10 programs per page.
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
         'title' : "View Dispersals",
        'page_obj': page_obj,
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
            form.save()
            return redirect('farm')  # Replace with your success redirect
    else:
        form = FarmLocationForm()
    
    grower_list = Grower.objects.all()  # Fetch growers for the dropdown
    
    return render(request, 'addfarmlocation.html', {
        'form': form,
        'grower_list': grower_list
    })