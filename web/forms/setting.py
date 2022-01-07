from django import forms
from django.core.exceptions import ValidationError

from web import models
from utils.tencent.cos import delete_bucket


class ProjectDeleteModelForm(forms.ModelForm):

    class Meta:
        model = models.Project
        fields = ['name', ]

    def __init__(self, request, *args, **kwargs):
        self.request = request
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = f'请输入{field.label}'

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name != self.request.project.name:
            raise ValidationError('请输入本项目的名称')
        project_object = models.Project.objects.filter(name=name, id=self.request.project.id).first()
        if project_object:
            if self.request.tracer == project_object.creator:
                delete_bucket(self.request.project.bucket, self.request.project.region)
                project_object.delete()
                return name
            raise ValidationError('只有项目创建者才可以删除项目')
        raise ValidationError('请输入正确的项目名称')
