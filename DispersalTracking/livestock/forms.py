from django import forms
from .models import Livestock, LivestockFamily, FarmLocation
from auth_user.models import Grower

class LivestockForm(forms.ModelForm):
    ls_code = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"}))
    
    gender = forms.ChoiceField(
        choices=Livestock.GENDER_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"}))
    
    generation = forms.IntegerField(
        widget=forms.TextInput(attrs={"class": "form-control"}))
    
    batch_no = forms.IntegerField(
        widget=forms.TextInput(attrs={"class": "form-control"}))
    
    age_in_days = forms.IntegerField(
        widget=forms.TextInput(attrs={"class": "form-control"}))

    livestock_family = forms.ModelChoiceField(
        required=False,
        queryset=LivestockFamily.objects.all(),
        widget=forms.Select(attrs={"class": "form-control"}))

    tag_color = forms.ChoiceField(
        required=False,  # Set to False if you want to allow custom input
        choices=[],  # Initially set to an empty list
        widget=forms.Select(attrs={"class": "form-control"})
    )

    class Meta:
        model = Livestock
        fields = ('ls_code', 'gender', 'generation', 'batch_no', 'age_in_days', 'livestock_family', 'tag_color')

    def __init__(self, *args, **kwargs):
        super(LivestockForm, self).__init__(*args, **kwargs)

        # Fetch unique tag colors from the database
        tag_colors = Livestock.objects.values_list('tag_color', flat=True).distinct()
        self.fields['tag_color'].choices = [(color, color) for color in tag_colors if color]  # Update choices

class LivestockFamilyForm(forms.ModelForm):
    family_id = forms.CharField(
        max_length=155, 
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter Family ID'
        })
    )
    
    cage_location = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter Cage Location'
        })
    )
    
    brood_generation_number = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter Brood Generation Number'
        }),
        initial=1
    )

    male_livestock = forms.ModelMultipleChoiceField(
        queryset=Livestock.objects.filter(gender='Male', livestock_family__isnull=True),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Select Males"
    )
    
    female_livestock = forms.ModelMultipleChoiceField(
        queryset=Livestock.objects.filter(gender='Female', livestock_family__isnull=True),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Select Females"
    )

    class Meta:
        model = LivestockFamily
        fields = ['family_id', 'cage_location', 'brood_generation_number']

    def save(self, commit=True):
        # Save the LivestockFamily instance first
        livestock_family = super().save(commit=True)

        # Updating selected livestock's livestock_family field after the family is saved
        male_livestock = self.cleaned_data['male_livestock']
        female_livestock = self.cleaned_data['female_livestock']
        
        # Update the livestock_family for male livestock
        for livestock in male_livestock:
            livestock.livestock_family = livestock_family
            livestock.save()

        # Update the livestock_family for female livestock
        for livestock in female_livestock:
            livestock.livestock_family = livestock_family
            livestock.save()

        return livestock_family

class FarmLocationForm(forms.ModelForm):
    class Meta:
        model = FarmLocation
        fields = ['name', 'address', 'description', 'grower']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
    
    # Adding hidden fields for latitude and longitude to be filled by Leaflet map
    latitude = forms.DecimalField(widget=forms.HiddenInput())
    longitude = forms.DecimalField(widget=forms.HiddenInput())