from django import forms
from .models import Grower, User, Farmer  # Import your custom User model

class UserForm(forms.ModelForm):
    user_name = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"}),
        label='Username',
        required=False
    )
    first_name = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"}),
        label='First Name',
        required=False
    )
    middle_name = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"}),
        label='Middle Name',
        required=False
    )
    last_name = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"}),
        label='Last Name',
        required=False
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"class": "form-control"}),
        label='Email',
        required=False
    )
    profile_picture = forms.ImageField(
        widget=forms.ClearableFileInput(attrs={"class": "form-control-file"}),
        label='Profile Picture',
        required=False
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        label='Password',
        required=False
    )

    class Meta:
        model = User
        fields = ['user_name', 'first_name', 'middle_name', 'last_name', 'email', 'profile_picture', 'password']
    
    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        # Map user_name to the actual username field
        self.fields['user_name'].initial = self.instance.username
        
class GrowerForm(forms.ModelForm):
    user_choice = forms.ChoiceField(
        choices=[('existing', 'Select Existing User'), ('none', 'None'), ('other', 'Create New User')],
        widget=forms.Select(attrs={"class": "form-control"}),
        initial='none',
        label='Link a User'
    )
    existing_user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=forms.Select(attrs={"class": "form-control", "style": "display: none;"}),
        label='Select Existing User'
    )
    new_user_first_name = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control", "style": "display: none;"}),
        required=False,
        label="New User First Name"
    )
    new_user_last_name = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control", "style": "display: none;"}),
        required=False,
        label="New User Last Name"
    )
    new_user_email = forms.EmailField(
        widget=forms.EmailInput(attrs={"class": "form-control", "style": "display: none;"}),
        required=False,
        label="New User Email"
    )
    
    ContactNo = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"}),
        required=False
    )
    Email = forms.EmailField(
        widget=forms.EmailInput(attrs={"class": "form-control"}),
        required=False
    )
    barangay = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"}),
        required=False
    )
    city = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"}),
        required=False
    )
    province = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"}),
        required=False
    )
    zipcode = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"}),
        required=False
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        required=False
    )

    class Meta:
        model = Grower
        fields = ['user_choice', 'existing_user', 'new_user_first_name', 'new_user_last_name', 'new_user_email', 
                  'ContactNo', 'Email', 'barangay', 'city', 'province', 'zipcode', 'notes']

    def save(self, commit=True):
        instance = super(GrowerForm, self).save(commit=False)

        user_choice = self.cleaned_data.get('user_choice')
        existing_user = self.cleaned_data.get('existing_user')

        if user_choice == 'existing' and existing_user:
            instance.linked_user = existing_user
            instance.first_name = existing_user.first_name
            instance.last_name = existing_user.last_name
            instance.Email = existing_user.email
        elif user_choice == 'other':
            new_user = User.objects.create(
                first_name=self.cleaned_data.get('new_user_first_name'),
                last_name=self.cleaned_data.get('new_user_last_name'),
                email=self.cleaned_data.get('new_user_email'),
                username=self.cleaned_data.get('new_user_email')  # Use email as username
            )
            instance.linked_user = new_user
            instance.first_name = new_user.first_name
            instance.last_name = new_user.last_name
            instance.Email = new_user.email
        else:
            instance.linked_user = None

        if commit:
            instance.save()
        return instance

class SimpleGrowerForm(forms.ModelForm):
    ContactNo = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"}),
        required=False
    )
    Email = forms.EmailField(
        widget=forms.EmailInput(attrs={"class": "form-control"}),
        required=False
    )
    barangay = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"}),
        required=False
    )
    city = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"}),
        required=False
    )
    province = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"}),
        required=False
    )
    zipcode = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"}),
        required=False
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        required=False
    )

    class Meta:
        model = Grower
        fields = ['ContactNo', 'Email', 'barangay', 'city', 'province', 'zipcode', 'notes']

    def clean(self):
        cleaned_data = super().clean()

        if not cleaned_data.get('ContactNo') and self.instance.pk:
            cleaned_data['ContactNo'] = self.instance.ContactNo

        if not cleaned_data.get('Email') and self.instance.pk:
            cleaned_data['Email'] = self.instance.Email

        return cleaned_data


class FarmerForm(forms.ModelForm):
    ContactNo = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"}),
        required=False
    )
    Email = forms.EmailField(
        widget=forms.EmailInput(attrs={"class": "form-control"}),
        required=False
    )

    class Meta:
        model = Farmer
        fields = ['ContactNo', 'Email']

    def clean(self):
        cleaned_data = super().clean()
        # Retain existing data if fields are empty
        if not cleaned_data.get('ContactNo') and self.instance.pk:
            cleaned_data['ContactNo'] = self.instance.ContactNo
        if not cleaned_data.get('Email') and self.instance.pk:
            cleaned_data['Email'] = self.instance.Email
        return cleaned_data


class FarmerForm2(forms.ModelForm):
    user_choice = forms.ChoiceField(
        choices=[('none', 'No User'), ('existing', 'Link to Existing User'), ('other', 'Create New User')],
        widget=forms.Select(attrs={"class": "form-control"})
    )
    existing_user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=forms.Select(attrs={"class": "form-control"})
    )

    ContactNo = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"}),
        required=False
    )
    Email = forms.EmailField(
        widget=forms.EmailInput(attrs={"class": "form-control"}),
        required=False
    )

    class Meta:
        model = Farmer
        fields = ['ContactNo', 'Email', 'user_choice', 'existing_user']
        

class FarmGrowerForm(forms.ModelForm):
    new_user_first_name = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"}),
        required=False,
        label="First Name"
    )
    new_user_last_name = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"}),
        required=False,
        label="Last Name"
    )
    new_user_email = forms.EmailField(
        widget=forms.EmailInput(attrs={"class": "form-control"}),
        required=False,
        label="Email"
    )
    
    ContactNo = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"}),
        required=False
    )
    barangay = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"}),
        required=False
    )
    city = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"}),
        required=False
    )
    province = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"}),
        required=False
    )
    zipcode = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"}),
        required=False
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        required=False
    )

    class Meta:
        model = Grower
        fields = [ 'new_user_first_name', 'new_user_last_name', 'new_user_email', 
                  'ContactNo', 'barangay', 'city', 'province', 'zipcode', 'notes']