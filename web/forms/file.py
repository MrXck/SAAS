from django import forms
from django.core.exceptions import ValidationError
from qcloud_cos import CosServiceError

from utils.tencent.cos import check_file
from web import models


class FolderModelForm(forms.ModelForm):

    class Meta:
        model = models.FileRepository
        fields = ['name', ]

    def __init__(self, request, parent_object, *args, **kwargs):
        self.request = request
        self.parent_object = parent_object
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = f'请输入{field.label}'

    def clean_name(self):
        name = self.cleaned_data.get('name')
        query_set = models.FileRepository.objects.filter(name=name, project=self.request.project, file_type=2)
        if self.parent_object:
            file_object = query_set.filter(parent=self.parent_object)
        else:
            file_object = query_set.filter(parent__isnull=True)
        if file_object:
            raise ValidationError('文件夹名称重复')
        return name


class FileModelForm(forms.ModelForm):

    etag = forms.CharField(label='Etag')

    def __init__(self, request, *args, **kwargs):
        self.request = request
        super().__init__(*args, **kwargs)

    class Meta:
        model = models.FileRepository
        fields = ['name', 'parent', 'file_size', 'file_path', 'key']

    def clean_file_path(self):
        return 'https://' + self.cleaned_data.get('file_path')

    def clean(self):
        etag = self.cleaned_data.get('etag')
        key = self.cleaned_data.get('key')
        size = self.cleaned_data.get('file_size')
        try:
            result = check_file(self.request.project.bucket, self.request.project.region, key)
        except CosServiceError as e:
            return self.add_error('key', '文件不存在')
        if etag != result.get('ETag'):
            return self.add_error('etag', 'Etag错误')
        if size != int(result.get('Content-Length')):
            return self.add_error('file_size', '文件大小错误')
        return self.cleaned_data
