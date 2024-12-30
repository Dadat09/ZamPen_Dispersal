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
        fields = ['user_choice', 'ContactNo', 'Email', 'barangay', 'city', 'province', 'zipcode', 'notes']

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(GrowerForm, self).__init__(*args, **kwargs)
        # Add a field to select existing users from the User model
        self.fields['existing_user'] = forms.ModelChoiceField(
            queryset=User.objects.all(),  # Query all existing users
            required=False,
            widget=forms.Select(attrs={'class': 'form-control'}),
            label='Select Existing User'
        )
        self.fields['existing_user'].widget.attrs['style'] = 'display: none;'  # Hide by default

        # Dynamically add fields for creating a new user if 'other' is selected
        if self.initial.get('user_choice') == 'other':
            self.fields['new_user_first_name'] = forms.CharField(
                widget=forms.TextInput(attrs={"class": "form-control"}),
                required=False
            )
            self.fields['new_user_last_name'] = forms.CharField(
                widget=forms.TextInput(attrs={"class": "form-control"}),
                required=False
            )
            self.fields['new_user_email'] = forms.EmailField(
                widget=forms.EmailInput(attrs={"class": "form-control"}),
                required=False
            )

    def save(self, commit=True):
        instance = super(GrowerForm, self).save(commit=False)
        if not instance.created_by_id:
            if self.request.user.is_authenticated:
                instance.created_by_id = self.request.user.id
            else:
                instance.created_by_id = 1
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
        widget=forms.Textarea(attrs={"class": "form-control", "rows": "4"}),
        required=False
    )

    class Meta:
        model = Grower
        fields = ['ContactNo', 'Email', 'barangay', 'city', 'province', 'zipcode', 'notes']

    def clean(self):
        """Ensure that empty fields retain the instance's existing values."""
        cleaned_data = super().clean()

        # Retain existing ContactNo if not provided
        if not cleaned_data.get('ContactNo') and self.instance.pk:
            cleaned_data['ContactNo'] = self.instance.ContactNo

        # Retain existing Email if not provided
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