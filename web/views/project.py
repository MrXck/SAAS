import time

from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse

from web.forms.project import ProjectModelForm
from web import models
from utils.tencent import cos


def project_list(request):
    if request.method == 'GET':
        form = ProjectModelForm()
        my_project_list = models.Project.objects.filter(creator=request.tracer)
        join_project_list = models.ProjectUser.objects.filter(user=request.tracer)
        project_dict = {'star': [], 'my': [], 'join': []}
        for i in my_project_list:
            if i.star:
                i.type = 'my'
                project_dict['star'].append(i)
            else:
                project_dict['my'].append(i)
        for i in join_project_list:
            if i.star:
                i.type = 'join'
                project_dict['star'].append(i.project)
            else:
                project_dict['join'].append(i.project)
        return render(request, 'project_list.html', {'form': form, 'project_dict': project_dict})
    form = ProjectModelForm(data=request.POST, request=request)
    if form.is_valid():

        # 创建桶
        bucket = f'{request.tracer.mobile_phone}-{str(int(time.time() * 1000))}-1308249213'
        region = 'ap-chengdu'
        cos.create_bucket(bucket, region)

        # 创建项目
        form.instance.bucket = bucket
        form.instance.region = region
        form.instance.creator = request.tracer
        instance = form.save()

        # 初始化项目问题类型
        li = []
        for i in models.IssuesType.PROJECT_INIT_LIST:
            li.append(models.IssuesType(project=instance, title=i))
        models.IssuesType.objects.bulk_create(li)
        return JsonResponse({'code': 0, 'data': reverse('web:project_list')})
    return JsonResponse({'code': 1, 'msg': form.errors})


def project_star(request, project_type, project_id):
    user = request.tracer
    if project_type == 'my':
        models.Project.objects.filter(creator=user, id=project_id).update(star=True)
    else:
        models.ProjectUser.objects.filter(project_id=project_id, user=user).update(star=True)
    return redirect(reverse('web:project_list'))


def project_unstar(request, project_type, project_id):
    user = request.tracer
    if project_type == 'my':
        models.Project.objects.filter(creator=user, id=project_id).update(star=False)
    else:
        models.ProjectUser.objects.filter(project_id=project_id, user=user).update(star=False)
    return redirect(reverse('web:project_list'))
