"""
URL configuration for DispersalTracking project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from livestock.views import ( indexView, AboutView, ContactView, ViewChickens, 
                            ViewFamilies, ViewFarms, ViewDispersals, addChickens, addLivestockFamily, 
                            addFarmLocation, addDispersal, editLivestock, editLivestockFamily, editFarmLocation, editDispersal, 
                            deleteLivestock, deleteFamily, deleteFarm, deleteDispersal, fetch_farms, dashboardView, exportfarmscsv,
                            downloadfarmspdf, MessagesView)
from auth_user.views import ViewGrowers, AddGrowers, editGrower, deleteGrower, userView, AddUser, EditUser, Deleteuser, ViewFarmers, AddFarmer, Deletefarmer, custom_login_view, logout_view
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', indexView, name="index" ),
    path('about/', AboutView, name='about'),
    path('contact/', ContactView, name='contact'),
    path('features/Livestock', ViewChickens, name = "livestock"),
    path('features/Families', ViewFamilies, name = "family"),
    path('features/Farms', ViewFarms, name = "farm"),
    path('features/Dispersals', ViewDispersals, name = "dispersal"),
    path('features/Growers', ViewGrowers, name = "grower"),
    path('features/Farmers', ViewFarmers, name = "farmer"),
    path('features/Messages', MessagesView, name = "messages"),
    path('features/Users', userView, name = "user"),
    path('features/Livestock/Add', addChickens, name = "addchickens"),
    path('features/Families/Add', addLivestockFamily, name = "addfamily"),
    path('features/Users/Add', AddUser, name = "adduser"),
    path('features/Farmers/Add', AddFarmer, name = "addfarmer"),
    path('features/Farms/Add', addFarmLocation, name = "addfarm"),
    path('features/Dispersals/Add', addDispersal, name = "adddispersal"),
    path('features/Users/edit/<int:pk>', EditUser, name = "editusers"),
    path('features/Livestock/edit/<int:pk>', editLivestock, name = "editchickens"),
    path('features/Family/edit/<int:pk>', editLivestockFamily, name='editfamily'),
    path('features/Farms/edit/<int:pk>', editFarmLocation, name='editfarm'),
    path('features/Dispersals/edit/<int:pk>', editDispersal, name="editdispersal"),
    path('features/Growers/Add', AddGrowers, name = "addgrower"),
    path('features/Growers/edit/<int:pk>', editGrower, name='editgrower'),
    path('features/Livestock/delete/<int:pk>/', deleteLivestock, name='delete_livestock'),
    path('features/Family/delete/<int:pk>/', deleteFamily, name='deletefamily'),
    path('features/Farmer/delete/<int:pk>/', Deletefarmer, name='deletefarmer'),
    path('features/Farms/delete/<int:pk>/', deleteFarm, name='deletefarm'),
    path('features/Dispersals/delete/<int:pk>', deleteDispersal, name='deletedispersal'),
    path('features/Growers/delete/<int:pk>', deleteGrower, name='deletegrower'),
    path('features/Users/delete/<int:id>', Deleteuser, name='deleteuser'),
    path('path/to/fetch/farms/', fetch_farms, name='fetch_farms'),
    path('dashboard/', dashboardView, name='dashboard'),
    path('export/farms_csv/', exportfarmscsv, name='export_farms_csv'),
    path('download/farms/pdf/', downloadfarmspdf, name='download_farms_pdf'),
    path('login/', custom_login_view, name='login'),
    path('logout/', logout_view, name='logout'),
]
