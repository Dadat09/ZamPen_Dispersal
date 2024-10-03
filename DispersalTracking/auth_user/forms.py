from django import forms
from .models import Grower, User  # Import your custom User model

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
        fields = ['first_name', 'middle_name', 'last_name', 'email', 'profile_picture', 'password', 'user_name']
        
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

