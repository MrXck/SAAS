import collections
import datetime
import time

from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import render
from web import models


def dashboard(request, project_id):
    status_dict = collections.OrderedDict()
    for key, text in models.Issues.status_choices:
        status_dict[key] = {'text': text, 'count': 0}
    issues_data = models.Issues.objects.filter(project_id=project_id).values('status').annotate(ct=Count('id'))
    for item in issues_data:
        status_dict[item['status']]['count'] = item['ct']

    user_list = models.ProjectUser.objects.filter(project_id=project_id).values_list('user_id', 'user__username')
    issues_list = models.Issues.objects.filter(project_id=project_id, assign__isnull=False).order_by('-id')[:10]
    return render(request, 'dashboard.html', {'status_dict': status_dict, 'user_list': user_list, 'issues_list': issues_list})


def issues_chart(request, project_id):
    today = datetime.datetime.now().date()
    result = models.Issues.objects.filter(project_id=project_id, create_datetime__gte=today - datetime.timedelta(days=30)).extra(
        select={'ctime': "DATE_FORMAT(web_issues.create_datetime, '%%Y-%%m-%%d')"}
    ).values('ctime').annotate(ct=Count('id'))
    date_dict = collections.OrderedDict()
    for i in range(0, 30):
        date = today - datetime.timedelta(days=i)
        date_dict[str(date.strftime('%Y-%m-%d'))] = [time.mktime(date.timetuple()) * 1000, 0]
    for i in result:
        date_dict[i['ctime']][1] = i['ct']
    return JsonResponse({'code': 0, 'data': list(date_dict.values())})
