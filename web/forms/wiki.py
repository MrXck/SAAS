from django import forms
from web import models


class WikiModelForm(forms.ModelForm):

    class Meta:
        model = models.Wiki
        fields = ['title', 'content', 'parent']

    def __init__(self, request, *args, **kwargs):
        self.request = request
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name == 'parent':
                data = [('', '请选择')] + list(models.Wiki.objects.filter(project_id=self.request.project.id).values_list('id', 'title'))
                field.choices = data
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = f'请输入{field.label}'
