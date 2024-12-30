from django import forms
from .models import Livestock, LivestockFamily, FarmLocation, Dispersal, Message
from django.db.models import Q 
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
        required=False,
        choices=[],  # Initially set to an empty list, will be populated in __init__
        widget=forms.Select(attrs={"class": "form-control"}))

    # Add the custom tag color field
    custom_tag_color = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Type a new tag color", "style": "display:none;"})
    )

    class Meta:
        model = Livestock
        fields = ('ls_code', 'gender', 'generation', 'batch_no', 'age_in_days', 'livestock_family', 'tag_color')

    def __init__(self, *args, **kwargs):
        super(LivestockForm, self).__init__(*args, **kwargs)

        # Fetch unique tag colors from the database
        tag_colors = Livestock.objects.values_list('tag_color', flat=True).distinct()
        self.fields['tag_color'].choices = [(color, color) for color in tag_colors if color]
        self.fields['tag_color'].choices.append(('other', 'Other'))  # Add 'Other' option

    def clean(self):
        cleaned_data = super().clean()
        tag_color = cleaned_data.get('tag_color')
        custom_tag_color = cleaned_data.get('custom_tag_color')

        # If 'Other' is selected, replace tag_color with custom_tag_color
        if tag_color == 'other' and custom_tag_color:
            cleaned_data['tag_color'] = custom_tag_color
        elif tag_color == 'other' and not custom_tag_color:
            self.add_error('custom_tag_color', "Please provide a custom tag color.")
        return cleaned_data

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
    name = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"}))
    
    address = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"}))
    
    description = forms.CharField(
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 4}))

    grower = forms.ModelChoiceField(
        queryset=Grower.objects.all(),
        widget=forms.Select(attrs={"class": "form-control"}))

    latitude = forms.DecimalField(
        widget=forms.TextInput(attrs={"class": "form-control"}),
        max_digits=9, decimal_places=6
    )
    longitude = forms.DecimalField(
        widget=forms.TextInput(attrs={"class": "form-control"}),
        max_digits=9, decimal_places=6
    )

    class Meta:
        model = FarmLocation
        fields = ['name', 'address', 'description', 'grower', 'latitude', 'longitude']

class DispersalForm(forms.ModelForm):
    grower = forms.ModelChoiceField(
        queryset=Grower.objects.all(),
        widget=forms.Select(attrs={"class": "form-control"})
    )
    
    dispersal_date = forms.DateField(
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"})
    )
    
    families_dispersed = forms.ModelMultipleChoiceField(
        queryset=LivestockFamily.objects.filter(dispersal__isnull=True),  # Initial queryset for new dispersal
        widget=forms.CheckboxSelectMultiple()
    )
    
    farmlocation = forms.ModelChoiceField(
        queryset=FarmLocation.objects.all(),
        widget=forms.Select(attrs={"class": "form-control"})
    )
    
    class Meta:
        model = Dispersal
        fields = ['grower', 'dispersal_date', 'families_dispersed', 'farmlocation']
    
    def __init__(self, *args, **kwargs):
        # Retrieve the instance (Dispersal object) being edited
        instance = kwargs.get('instance', None)
        
        super(DispersalForm, self).__init__(*args, **kwargs)

        if instance:
            # Get the families already associated with the current dispersal
            current_families = instance.families_dispersed.all()
            
            # Include both the families not yet dispersed and the current families of this dispersal
            self.fields['families_dispersed'].queryset = LivestockFamily.objects.filter(
                Q(dispersal__isnull=True) | Q(family_id__in=current_families)
            )

            # Preselect the families already dispersed to this instance
            self.fields['families_dispersed'].initial = current_families

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['name', 'email', 'message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Enter your message'}),
            'name': forms.TextInput(attrs={'placeholder': 'Enter your name'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Enter your email'}),
        }
        labels = {
            'name': 'Your Name',
            'email': 'Your Email',
            'message': 'Your Message',
        }
    def __init__(self, *args, **kwargs):
        super(MessageForm, self).__init__(*args, **kwargs)
        self.fields['name'].widget.attrs.update({'class': 'w-100'})
        self.fields['email'].widget.attrs.update({'class': 'w-100'})
        self.fields['message'].widget.attrs.update({'class': 'w-100'})