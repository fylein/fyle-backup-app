from django import forms
from tempus_dominus.widgets import DatePicker


class ExpenseForm(forms.Form):
    """
    Expenses form
    """
    data_format_choices = [
        ("CSV", "CSV")
    ]
    expense_state_choices = [
        ('FYLED', 'FYLED'),
        ('PAID', 'PAID'),
        ('APPROVED', 'APPROVED'),
        ('DRAFT', 'DRAFT'),
        ('APPROVER_PENDING', 'APPROVER PENDING'),
        ('COMPLETE', 'COMPLETE'),
        ('PAYMENT_PROCESSING', 'PAYMENT PROCESSING'),
        ('PAYMENT_PENDING', 'PAYMENT PENDING')]
    name = forms.CharField(max_length=64, label='Name*',
                           widget=forms.TextInput(
                               attrs={
                                   'placeholder': 'Provide a name for this backup',
                                   'autocomplete': 'off'
                               }))
    data_format = forms.ChoiceField(widget=forms.HiddenInput(),
                                    choices=data_format_choices,
                                    initial='CSV')
    object_type = forms.CharField(
        widget=forms.HiddenInput(), initial='expenses')
    state = forms.MultipleChoiceField(choices=expense_state_choices,
                                      required=False
                                      )
    approved_at_gte = forms.DateField(widget=DatePicker(
        attrs={
            'icon_toggle': True,
            'append': 'fa fa-calendar',
            'class': 'icon-calendar'
        }
    ), required=False)
    approved_at_lte = forms.DateField(widget=DatePicker(
        attrs={
            'icon_toggle': True,
            'append': 'fa fa-calendar'
        }
    ), required=False)
    updated_at_gte = forms.DateField(widget=DatePicker(
        attrs={
            'icon_toggle': True,
            'append': 'fa fa-calendar'
        }
    ), required=False)
    updated_at_lte = forms.DateField(widget=DatePicker(
        attrs={
            'icon_toggle': True,
            'append': 'fa fa-calendar'
        }
    ), required=False)
    download_attachments = forms.BooleanField(required=False)
