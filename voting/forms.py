from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .models import Election, Vote, Candidate


class VoteForm(forms.ModelForm):
    """Form for casting a vote in an election."""
    class Meta:
        model = Vote
        fields = ['candidate']
        widgets = {
            'candidate': forms.RadioSelect(),
        }

    def __init__(self, *args, **kwargs):
        self.election = kwargs.pop('election', None)
        super().__init__(*args, **kwargs)
        
        if self.election:
            self.fields['candidate'].queryset = Candidate.objects.filter(
                position__election=self.election
            )
            
        # Add Bootstrap classes to form fields
        for field in self.fields:
            if field != 'candidate':  # Skip for RadioSelect widget
                self.fields[field].widget.attrs.update({'class': 'form-control'})

    def clean(self):
        cleaned_data = super().clean()
        # Add any additional validation if needed
        return cleaned_data


class CandidateForm(forms.ModelForm):
    """Form for creating and updating candidates."""
    class Meta:
        model = Candidate
        fields = ['user', 'bio', 'photo', 'position', 'manifesto']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
            'manifesto': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to form fields
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

class ElectionForm(forms.ModelForm):
    class Meta:
        model = Election
        fields = ['name', 'description', 'start_date', 'end_date', 'is_public']
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set the datetime input format for proper rendering
        self.fields['start_date'].input_formats = ['%Y-%m-%dT%H:%M']
        self.fields['end_date'].input_formats = ['%Y-%m-%dT%H:%M']
        
        # Add Bootstrap classes to form fields
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date:
            if start_date >= end_date:
                raise forms.ValidationError(_('End date must be after start date.'))
            
            if start_date < timezone.now():
                raise forms.ValidationError(_('Start date cannot be in the past.'))
        
        return cleaned_data
