from django.shortcuts import render, redirect
from django.urls import reverse

from web import models
from web.forms.setting import ProjectDeleteModelForm


def setting(request, project_id):
    return render(request, 'setting.html')


def delete(request, project_id):
    if request.method == 'GET':
        form = ProjectDeleteModelForm(request=request)
        return render(request, 'setting_delete.html', {'form': form})
    form = ProjectDeleteModelForm(request=request, data=request.POST)
    if form.is_valid():
        return redirect(reverse('web:project_list'))
    return render(request, 'setting_delete.html', {'form': form})
