from django import forms
from .models import Truck, Booking

class TruckForm(forms.ModelForm):
    class Meta:
        model = Truck
        fields = ['name', 'image', 'weight_range', 'available']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter truck name'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'weight_range': forms.Select(attrs={'class': 'form-control'}),
        }

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['product_name', 'product_weight', 'product_value', 'phone_number', 'pickup_state', 'destination_state',]
        widgets = {
            'product_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter product name'}),
            'product_weight': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter product weight'}),
            'product_value': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter product value'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter phone number'}),
            'pickup_state': forms.Select(attrs={'class': 'form-control'}),
            'destination_state': forms.Select(attrs={'class': 'form-control'}),
        }



class TruckApprovalForm(forms.Form):
    truck_ids = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    def __init__(self, *args, **kwargs):
        super(TruckApprovalForm, self).__init__(*args, **kwargs)
        self.fields['truck_ids'].choices = [
            (truck.id, f'{truck.name} - Owned by {truck.owner.username}') 
            for truck in Truck.objects.filter(available=False)
        ]
