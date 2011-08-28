from django import forms
from django.forms.fields import DateField
from django.shortcuts import get_object_or_404
from annotations.models import Label
from images.models import Source, Value1, Value2, Value3, Value4, Value5, Metadata
from django.forms.extras.widgets import SelectDateWidget

MODE_CHOICES = (
    ('image', 'View whole images'),
    ('patch', 'View patches'),
)

DATE_CHOICES = ()
class YearModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, Metadata):
        return Metadata.photo_date.year
        

class VisualizationSearchForm(forms.Form):
    def __init__(self,source_id,*args,**kwargs):
        super(VisualizationSearchForm,self).__init__(*args,**kwargs)
        source = get_object_or_404(Source,id=source_id)

        #Gets options to show for each value that the user selects
        self.fields['value1'].queryset = Value1.objects.filter(source=source)
        self.fields['value2'].queryset = Value2.objects.filter(source=source)
        self.fields['value3'].queryset = Value3.objects.filter(source=source)
        self.fields['value4'].queryset = Value4.objects.filter(source=source)
        self.fields['value5'].queryset = Value5.objects.filter(source=source)
        self.fields['year'].queryset = Metadata.objects.filter(image__source=source).distinct()
        self.fields['labels'].queryset = Label.objects.filter(labelset__id=source.labelset_id).distinct()

    value1 = forms.ModelChoiceField(queryset=(), empty_label="All", required=False)
    value2 = forms.ModelChoiceField(queryset=(), empty_label="All", required=False)
    value3 = forms.ModelChoiceField(queryset=(), empty_label="All", required=False)
    value4 = forms.ModelChoiceField(queryset=(), empty_label="All", required=False)
    value5 = forms.ModelChoiceField(queryset=(), empty_label="All", required=False)
    year = YearModelChoiceField(queryset=(), empty_label="All", required=False)
    mode = forms.ChoiceField(choices=MODE_CHOICES)
    labels = forms.ModelChoiceField(queryset=(), empty_label="All", required=False)
