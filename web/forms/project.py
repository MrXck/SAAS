from django import forms
from web import models
from django.core.exceptions import ValidationError
from web.forms.widgets import ColorRadioSelect


class ProjectModelForm(forms.ModelForm):

    class Meta:
        model = models.Project
        fields = ['name', 'color', 'desc']
        widgets = {
            'desc': forms.Textarea,
            'color': ColorRadioSelect(attrs={'class': 'color-radio'})
        }

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name != 'color':
                field.widget.attrs['class'] = 'form-control'
                field.widget.attrs['placeholder'] = f'请输入{field.label}'

    def clean_name(self):
        user = self.request.tracer
        name = self.cleaned_data.get('name')
        project_list = models.Project.objects.filter(creator=user)
        is_have_name = project_list.filter(name=name)
        if is_have_name:
            raise ValidationError('已存在同名项目')
        count = project_list.count()
        if count >= self.request.price_policy.project_num:
            raise ValidationError('创建的项目已到达限制')
        return name


