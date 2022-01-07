from django import template
from django.urls import reverse

from web import models


register = template.Library()


@register.inclusion_tag('inclusion/all_project_list.html')
def all_project_list(request):
    user = request.tracer
    my_project_list = models.Project.objects.filter(creator=user)
    join_project_list = models.ProjectUser.objects.filter(user=user)
    return {'my': my_project_list, 'join': join_project_list, 'project': request.project}


@register.inclusion_tag('inclusion/manage_menu_list.html')
def manage_menu_list(request):
    data = [
        {'title': '概览', 'url': reverse('web:dashboard', kwargs={'project_id': request.project.id}), 'active': False},
        {'title': '问题', 'url': reverse('web:issues', kwargs={'project_id': request.project.id}), 'active': False},
        {'title': '统计', 'url': reverse('web:statistics', kwargs={'project_id': request.project.id}), 'active': False},
        {'title': '文件', 'url': reverse('web:file', kwargs={'project_id': request.project.id}), 'active': False},
        {'title': 'wiki', 'url': reverse('web:wiki', kwargs={'project_id': request.project.id}), 'active': False},
        {'title': '设置', 'url': reverse('web:setting', kwargs={'project_id': request.project.id}), 'active': False},
    ]
    for i in data:
        if request.path_info.startswith(i['url']):
            i['active'] = True
    return {'data': data}
