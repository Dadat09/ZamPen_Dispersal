from django.shortcuts import render
from django.views.generic import TemplateView
from .models import *
from django.core.paginator import Paginator
from django.db.models import Q

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
    query = request.GET.get('q')
    Livestocks = Livestock.objects.all()  # Add () here
    tag_color_filter = request.GET.get('tag_color', None)
    unique_tag_colors = Livestock.objects.values_list('tag_color', flat=True).distinct()

    if query:
        Livestocks = Livestocks.filter( 
            Q(id__icontains=query) |
            Q(gender__icontains=query)|
            Q(batch_no__icontains=query)|
            Q(tag_color__icontains=query)
        )

    if tag_color_filter:
        Livestocks =  Livestocks.filter(tag_color=tag_color_filter)

    paginator = Paginator(Livestocks, 10)  # Show 10 programs per page.
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'title' : "View Chicken",
        'page_obj': page_obj,
        'unique_tag_colors': unique_tag_colors,
    }

    return render(request, 'viewchickens.html', context)

def ViewFamilies(request):
    query = request.GET.get('q')
    families = LivestockFamily.objects.all()
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

def ViewFarms(request):
    query = request.GET.get('q')
    farms = FarmLocation.objects.all()
    if query:
        farms = farms.filter( 
            Q(name__icontains=query) |
            Q(address__icontains=query)
        )

    paginator = Paginator(farms, 10)  # Show 10 programs per page.
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
         'title' : "View Farms",
        'page_obj': page_obj,
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