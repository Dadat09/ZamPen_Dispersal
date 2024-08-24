from django.shortcuts import render
from django.views.generic import TemplateView

def indexView(request):
    title = 'Zampen Chicken Dispersal'
    context = {
        'title':title
    }
    return render(request, 'index.html', context)


class AboutView(TemplateView):
    template_name = 'about.html'

class ContactView(TemplateView):
    template_name = 'contact.html'