import collections

from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import render

from web import models


def statistics(request, project_id):
    return render(request, 'statistics.html')


def statistics_priority(request, project_id):
    data_dict = collections.OrderedDict()
    for key, text in models.Issues.priority_choices:
        data_dict[key] = {'name': text, 'y': 0}
    issues_object_list = models.Issues.objects.filter(project_id=project_id, create_datetime__gte=request.GET.get('start_date'), create_datetime__lt=request.GET.get('end_date')).values('priority').annotate(ct=Count('id'))
    for i in issues_object_list:
        data_dict[i['priority']]['y'] = i['ct']
    return JsonResponse({'code': 0, 'data': list(data_dict.values())})


def statistics_project_user(request, project_id):
    all_user_dict = collections.OrderedDict()
    all_user_dict[None] = {
        'name': '未指派',
        'status': {i[0]: 0 for i in models.Issues.status_choices}
    }
    project_user_list = list(models.ProjectUser.objects.filter(project_id=project_id).values_list('user_id', 'user__username')) + [(request.project.creator.id, request.project.creator.username)]
    for item in project_user_list:
        all_user_dict[item[0]] = {'name': item[1], 'status': {i[0]: 0 for i in models.Issues.status_choices}}
    issues_list = models.Issues.objects.filter(project_id=project_id, create_datetime__gte=request.GET.get('start_date'), create_datetime__lt=request.GET.get('end_date'))
    for item in issues_list:
        if not item.assign:
            all_user_dict[None]['status'][item.status] += 1
        all_user_dict[item.assign_id]['status'][item.status] += 1
    categories = [data['name'] for data in all_user_dict.values()]
    data_result_dict = collections.OrderedDict()
    for item in models.Issues.status_choices:
        data_result_dict[item[0]] = {'name': item[1], 'data': []}
    for key, text in models.Issues.status_choices:
        for k, v in all_user_dict.items():
            data_result_dict[key]['data'].append(v['status'][key])
    return JsonResponse({'code': 0, 'data': {'categories': categories, 'series': list(data_result_dict.values())}})
