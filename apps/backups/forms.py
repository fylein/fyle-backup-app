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
        ('COMPLETE', 'FYLED'),
        ('PAID', 'PAID'),
        ('APPROVED', 'APPROVED'),
        ('DRAFT', 'DRAFT'),
        ('APPROVER_PENDING', 'APPROVER PENDING'),
        ('PAYMENT_PROCESSING', 'PAYMENT PROCESSING'),
        ('PAYMENT_PENDING', 'PAYMENT PENDING')]

    fund_source_choices = [
        ('PERSONAL', 'Personal Account'),
        ('ADVANCE', 'Advance'),
        ('CCC', 'Corporate Credit Card')]

    reimbursable_choices = [
        (True, 'Yes'),
        (False, 'No')]

    name = forms.CharField(
        max_length=64,
        label='Name*',
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Provide a name for this backup',
                'autocomplete': 'off'}))
    data_format = forms.ChoiceField(widget=forms.HiddenInput(),
                                    choices=data_format_choices,
                                    initial='CSV')
    object_type = forms.CharField(
        widget=forms.HiddenInput(), initial='expenses')
    state = forms.MultipleChoiceField(choices=expense_state_choices,
                                      required=False
                                      )
    fund_source = forms.MultipleChoiceField(choices=fund_source_choices,
                                            required=False
                                            )
    reimbursable = forms.ChoiceField(choices=reimbursable_choices,
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
    reimbursed_at_gte = forms.DateField(widget=DatePicker(
        attrs={
            'icon_toggle': True,
            'append': 'fa fa-calendar'
        }
    ), required=False)
    reimbursed_at_lte = forms.DateField(widget=DatePicker(
        attrs={
            'icon_toggle': True,
            'append': 'fa fa-calendar'
        }
    ), required=False)
    spent_at_gte = forms.DateField(widget=DatePicker(
        attrs={
            'icon_toggle': True,
            'append': 'fa fa-calendar'
        }
    ), required=False)
    spent_at_lte = forms.DateField(widget=DatePicker(
        attrs={
            'icon_toggle': True,
            'append': 'fa fa-calendar'
        }
    ), required=False)
    download_attachments = forms.BooleanField(required=False)
