from django import forms

from web import models


class IssuesModelForm(forms.ModelForm):

    class Meta:
        model = models.Issues
        exclude = ['project', 'creator', 'create_datetime', 'latest_update_datetime']
        widgets = {
            'desc': forms.Textarea(),
            'start_date': forms.TextInput(attrs={'type': 'date'}),
            'end_date': forms.TextInput(attrs={'type': 'date'}),
            'assign': forms.Select(attrs={'class': 'form-control selectpicker', 'data-live-search': 'true'}),
            'parent': forms.Select(attrs={'class': 'form-control selectpicker', 'data-live-search': 'true'}),
            'attention': forms.SelectMultiple(attrs={'class': 'form-control selectpicker', 'data-live-search': 'true', 'data-actions-box': 'true'}),
        }

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['issues_type'].choices = models.IssuesType.objects.filter(project=request.project).values_list('id', 'title')
        user_list = [(request.project.creator.id, request.project.creator.username)] + list(models.ProjectUser.objects.filter(project=request.project).values_list('user_id', 'user__username'))
        self.fields['assign'].choices = [('', '没有选中任何项'), ] + user_list
        self.fields['attention'].choices = user_list
        self.fields['module'].choices = [('', '没有选中任何项'), ] + list(models.Module.objects.filter(project=request.project).values_list('id', 'title'))
        self.fields['parent'].choices = [('', '没有选中任何项'), ] + list(models.Issues.objects.filter(project=request.project).values_list('id', 'subject'))
        for name, field in self.fields.items():
            if name == 'assign' or name == 'attention' or name == 'parent':
                continue
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = f'请输入{field.label}'


class IssuesReplyModelForm(forms.ModelForm):

    class Meta:
        model = models.IssuesReply
        fields = ['content', 'reply']


class InviteModelForm(forms.ModelForm):

    class Meta:
        model = models.ProjectInvite
        fields = ['period', 'count']

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = f'请输入{field.label}'

