import json

import requests
from django.http import JsonResponse, HttpResponse, FileResponse
from django.shortcuts import render
from django.utils.encoding import escape_uri_path
from django.views.decorators.csrf import csrf_exempt

from web.forms.file import FileModelForm, FolderModelForm
from web import models
from utils.tencent.cos import delete_file, delete_file_list, credential


def file(request, project_id):
    folder_id = request.GET.get('folder_id', '')
    parent_object = None
    if folder_id.isdecimal():
        parent_object = models.FileRepository.objects.filter(project_id=project_id, id=folder_id, file_type=2).first()
    if request.method == 'GET':
        breadcrumb_list = []
        parent = parent_object
        while parent:
            breadcrumb_list.insert(0, parent)
            parent = parent.parent
        form = FolderModelForm(request=request, parent_object=parent_object)
        query_set = models.FileRepository.objects.filter(project_id=project_id)
        if parent_object:
            file_object_list = query_set.filter(parent=parent_object).order_by('-file_type')
        else:
            file_object_list = query_set.filter(parent__isnull=True).order_by('-file_type')
        file_object_list = file_object_list
        return render(request, 'file.html', {'form': form, 'file_object_list': file_object_list, 'breadcrumb_list': breadcrumb_list, 'parent_object': parent_object})
    fid = request.POST.get('fid', '')
    if fid.isdecimal():
        file_object = models.FileRepository.objects.filter(id=fid, project_id=project_id, file_type=2).first()
        form = FolderModelForm(request=request, parent_object=parent_object, data=request.POST, instance=file_object)
    else:
        form = FolderModelForm(request=request, parent_object=parent_object, data=request.POST)
    if form.is_valid():
        form.instance.project = request.project
        form.instance.file_type = 2
        form.instance.update_user = request.tracer
        form.instance.parent = parent_object
        form.save()
        return JsonResponse({'code': 0})
    return JsonResponse({'code': 1, 'msg': form.errors})


def file_delete(request, project_id):
    fid = request.GET.get('fid', '')
    if fid.isdecimal():
        delete_object = models.FileRepository.objects.filter(id=fid, project_id=project_id).first()
        if delete_object.file_type == 1:
            delete_file(request.project.bucket, request.project.region, delete_object.key)
            delete_object.delete()
            request.project.use_space -= delete_object.file_size
            request.project.save()
        else:
            total_size = 0
            key_list = []
            folder_list = [delete_object, ]
            for folder in folder_list:
                child_list = models.FileRepository.objects.filter(project_id=project_id, parent=folder).order_by('-file_type')
                for child in child_list:
                    if child.file_type == 2:
                        folder_list.append(child)
                    else:
                        total_size += child.file_size
                        key_list.append({'Key': child.key})
            if key_list:
                delete_file_list(request.project.bucket, request.project.region, key_list)
            if total_size:
                request.project.use_space -= total_size
                request.project.save()
            delete_object.delete()
        return JsonResponse({'code': 0})
    return JsonResponse({'code': 1, 'error': '请输入正常的数字'})


@csrf_exempt
def cos_credential(request, project_id):
    file_list = json.loads(request.body.decode('utf-8'))
    total = 0
    per_file_size = request.price_policy.per_file_size * 1024 * 1024
    for item in file_list:
        if item['size'] > per_file_size:
            return JsonResponse({'code': 1, 'error': f"{item['name']}文件大小超过限制，单文件最大为{request.price_policy.per_file_size}M"})
        total += item['size']
    if total > request.price_policy.project_space * 1024 * 1024 * 1024 - request.project.use_space:
        return JsonResponse({'code': 1, 'error': '已超过此项目的总容量'})
    data = credential(request.project.bucket, request.project.region)
    return JsonResponse({'code': 0, 'data': data})


@csrf_exempt
def file_upload(request, project_id):
    form = FileModelForm(request=request, data=request.POST)
    if form.is_valid():
        data_dict = form.cleaned_data
        data_dict.pop('etag')
        data_dict['project'] = request.project
        data_dict['file_type'] = 1
        data_dict['update_user'] = request.tracer
        instance = models.FileRepository.objects.create(**data_dict)
        request.project.use_space += data_dict['file_size']
        request.project.save()
        result = {
            'name': instance.name,
            'id': instance.id,
            'file_size': instance.file_size,
            'update_user': instance.update_user.username,
            'update_datetime': instance.update_datetime.strftime('%Y{}%m{}%d{} %H:%M').format('年', '月', '日'),
            'file_path': instance.file_path
        }
        return JsonResponse({'code': 0, 'data': result})
    return JsonResponse({'code': 1, 'error': form.errors})


def file_download(request, project_id):
    fid = request.GET.get('fid', '')
    if not fid.isdecimal():
        return HttpResponse('找不到此文件')
    file_object = models.FileRepository.objects.filter(id=fid, project_id=project_id).first()
    res = requests.get(url=file_object.file_path)
    response = FileResponse(res.iter_content())
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Length'] = len(res.content)
    response['Content-Disposition'] = 'attachment;filename="{}"'.format(escape_uri_path(file_object.name))
    return response
