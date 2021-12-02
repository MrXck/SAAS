import datetime
import json

from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.views.decorators.csrf import csrf_exempt

from utils.encrypt import uid
from utils.pagination import Pagination
from web.forms.issues import IssuesModelForm, IssuesReplyModelForm, InviteModelForm
from web import models


class CheckFilter(object):
    def __init__(self, name, data_list, request):
        self.data_list = data_list
        self.request = request
        self.name = name

    def __iter__(self):
        for item in self.data_list:
            ck = ''
            value_list = self.request.GET.getlist(self.name)
            if str(item[0]) in value_list:
                ck = 'checked'
                value_list.remove(str(item[0]))
            else:
                value_list.append(str(item[0]))
            query_dict = self.request.GET.copy()
            query_dict._mutable = True
            query_dict.setlist(self.name, value_list)
            if 'page' in query_dict:
                query_dict.pop('page')
            yield mark_safe(f'<a class="cell" href="{self.request.path_info}?{query_dict.urlencode()}"><input type="checkbox" {ck} /><label for="">{item[1]}</label></a>')


class SelectFilter(object):
    def __init__(self, name, data_list, request):
        self.data_list = data_list
        self.request = request
        self.name = name

    def __iter__(self):

        yield mark_safe('<select class="select2" multiple style="width:100%;">')
        for item in self.data_list:
            selected = ''
            value_list = self.request.GET.getlist(self.name)
            if str(item[0]) in value_list:
                selected = 'selected'
                value_list.remove(str(item[0]))
            else:
                value_list.append(str(item[0]))
            query_dict = self.request.GET.copy()
            query_dict._mutable = True
            query_dict.setlist(self.name, value_list)
            if 'page' in query_dict:
                query_dict.pop('page')
            yield mark_safe(f'<option value="{self.request.path_info}?{query_dict.urlencode()}" {selected}>{item[1]}</option>')
        yield mark_safe('</select>')


def issues(request, project_id):
    if request.method == 'GET':
        allow_filter_name = ['issues_type', 'status', 'priority', 'assign', 'attention']
        condition = {}
        for name in allow_filter_name:
            value_list = request.GET.getlist(name)
            if not value_list:
                continue
            condition[name + '__in'] = value_list
        queryset = models.Issues.objects.filter(project_id=project_id).filter(**condition)
        page = request.GET.get('page')
        if not page:
            page = 1
        page_object = Pagination(
            current_page=page,
            all_count=queryset.count(),
            base_url=request.path_info,
            query_params=request.GET,
            per_page=10
        )
        issues_object_list = queryset[page_object.start:page_object.end]
        form = IssuesModelForm(request=request)
        invite = InviteModelForm(request=request)
        project_total_user = [(request.project.creator_id, request.project.creator.username), ]
        project_total_user += list(models.ProjectUser.objects.filter(project_id=project_id).values_list('user_id', 'user__username'))
        return render(request, 'issues.html', {
            'form': form,
            'invite': invite,
            'issues_object_list': issues_object_list,
            'page_html': page_object.page_html(),
            'status_filter': CheckFilter('status', models.Issues.status_choices, request),
            'priority_filter': CheckFilter('priority', models.Issues.priority_choices, request),
            'issues_type_filter': CheckFilter('issues_type', models.IssuesType.objects.filter(project_id=project_id).values_list('id', 'title'), request),
            'assign': SelectFilter('assign', project_total_user, request),
            'attention': SelectFilter('attention', project_total_user, request),
        })
    form = IssuesModelForm(request=request, data=request.POST)
    if form.is_valid():
        data = form.cleaned_data
        data['project'] = request.project
        data['creator'] = request.tracer
        data.pop('attention')
        issues_object = models.Issues.objects.create(**data)
        issues_object.attention.add(*request.POST.getlist('attention'))
        return JsonResponse({'code': 0})
    return JsonResponse({'code': 1, 'msg': form.errors})


def issues_detail(request, project_id, issues_id):
    issues_object = models.Issues.objects.filter(id=issues_id, project_id=project_id).first()
    if request.method == 'GET':
        form = IssuesModelForm(instance=issues_object, request=request)
        return render(request, 'issues_detail.html', {'form': form, 'issues_object': issues_object})


@csrf_exempt
def issues_record(request, project_id, issues_id):
    if request.method == 'GET':
        reply_list = models.IssuesReply.objects.filter(issues__project_id=project_id, issues_id=issues_id)
        data_list = []
        for reply in reply_list:
            data = {
                'id': reply.id,
                'reply_type_text': reply.get_reply_type_display(),
                'content': reply.content,
                'creator': reply.creator.username,
                'datetime': reply.create_datetime.strftime("%Y-%m-%d %H:%M"),
                'parent_id': reply.reply_id,
            }
            data_list.append(data)
        return JsonResponse({'code': 0, 'data': data_list})
    form = IssuesReplyModelForm(data=request.POST)
    if form.is_valid():
        form.instance.issues_id = issues_id
        form.instance.reply_type = 2
        form.instance.creator = request.tracer
        instance = form.save()
        data = {
            'id': instance.id,
            'reply_type_text': instance.get_reply_type_display(),
            'content': instance.content,
            'creator': instance.creator.username,
            'datetime': instance.create_datetime.strftime("%Y-%m-%d %H:%M"),
            'parent_id': instance.reply_id,
        }
        return JsonResponse({'code': 0, 'data': data})
    return JsonResponse({'code': 1, 'msg': form.errors})


@csrf_exempt
def issues_change(request, project_id, issues_id):
    post_dict = json.loads(request.body.decode('utf-8'))
    name = post_dict.get('name')
    value = post_dict.get('value')
    issues_object = models.Issues.objects.filter(project_id=project_id, id=issues_id).first()
    field_object = models.Issues._meta.get_field(name)
    if name in ['desc', 'subject', 'start_date', 'end_date']:
        if not value:
            if not field_object.null:
                return JsonResponse({'code': 1, 'msg': {name: f'{field_object.verbose_name}不能为空'}})
            setattr(issues_object, name, None)
            issues_object.save()
            msg = f'{field_object.verbose_name}更新为空'
        else:
            setattr(issues_object, name, value)
            issues_object.save()
            msg = f'{field_object.verbose_name}更新为{value}'
    elif name in ['issues_type', 'module', 'parent', 'assign']:
        if not value:
            if not field_object.null:
                return JsonResponse({'code': 1, 'msg': {name: f'{field_object.verbose_name}不能为空'}})
            setattr(issues_object, name, None)
            issues_object.save()
            msg = f'{field_object.verbose_name}更新为空'
        else:
            if name == 'assign':
                if value == str(request.project.creator_id):
                    instance = request.project.creator
                else:
                    project_user_project = models.ProjectUser.objects.filter(project_id=project_id, user_id=value).first()
                    if project_user_project:
                        instance = project_user_project.user
                    else:
                        instance = None
                if not instance:
                    return JsonResponse({'code': 1, 'msg': {name: f'你选择的值不存在'}})
            else:
                instance = field_object.rel.model.objects.filter(project_id=project_id, id=value).first()
                if not instance:
                    return JsonResponse({'code': 1, 'msg': {name: f'你选择的值不存在'}})
            setattr(issues_object, name, instance)
            issues_object.save()
            msg = f'{field_object.verbose_name}更新为{str(instance)}'
    elif name in ['status', 'priority', 'mode']:
        selected_text = None
        for key, text in field_object.choices:
            if str(key) == value:
                selected_text = text
        if not selected_text:
            return JsonResponse({'code': 1, 'msg': {name: f'你选择的值不存在'}})
        setattr(issues_object, name, value)
        issues_object.save()
        msg = f'{field_object.verbose_name}更新为{selected_text}'
    elif name == 'attention':
        if isinstance(value, list):
            return JsonResponse({'code': 1, 'msg': {name: f'数据格式错误'}})
        if not value:
            issues_object.attention.set([])
            issues_object.save()
            msg = f'{field_object.verbose_name}更新为空'
        else:
            user_dict = {str(request.project.creator_id): request.project.creator.username}
            project_user_list = models.ProjectUser.objects.filter(project_id=project_id)
            for project_user in project_user_list:
                user_dict[str(project_user.user_id)] = project_user.user.username
            username_list = []
            for user_id in value:
                username = user_dict.get(str(user_id))
                if not username:
                    return JsonResponse({'code': 1, 'msg': {name: f'用户不存在，请刷新'}})
                username_list.append(username)
            issues_object.attention.set(value)
            issues_object.save()
            msg = f'{field_object.verbose_name}更新为{",".join(username_list)}'
    else:
        return JsonResponse({'code': 2, 'msg': 'xxx'})

    instance = models.IssuesReply.objects.create(
        creator=request.tracer,
        issues_id=issues_id,
        content=msg,
        reply_type=1,
    )
    data = {
        'id': instance.id,
        'reply_type_text': instance.get_reply_type_display(),
        'content': instance.content,
        'creator': instance.creator.username,
        'datetime': instance.create_datetime.strftime("%Y-%m-%d %H:%M"),
        'parent_id': instance.reply_id,
    }
    return JsonResponse({'code': 0, 'data': data})


def invite_url(request, project_id):
    form = InviteModelForm(request=request, data=request.POST)
    if form.is_valid():
        if request.tracer != request.project.creator:
            form.add_error('period', '只有项目创建者才能邀请')
            return JsonResponse({'code': 1, 'msg': form.errors})
        code = uid(request.tracer.mobile_phone)
        form.instance.creator = request.tracer
        form.instance.project = request.project
        form.instance.code = code
        form.save()
        url = f"{request.scheme}://{request.get_host()}{reverse('web:invite_join', kwargs={'code': code})}"
        return JsonResponse({'code': 0, 'data': url})
    return JsonResponse({'code': 1, 'msg': form.errors})


def invite_join(request, code):
    invite_object = models.ProjectInvite.objects.filter(code=code).first()
    if invite_object:
        now = datetime.datetime.now()
        if request.tracer == request.project.creator or models.ProjectUser.objects.filter(project_id=invite_object.project_id, user=request.tracer):
            return render(request, 'invite_join.html', {'error': '你已经在这个项目当中了'})
        max_transaction = models.Transaction.objects.filter(user=invite_object.project.creator).order_by('-id').first()
        if max_transaction.price_policy.category == 1:
            max_member = max_transaction.price_policy.project_member
        else:
            if max_transaction.end_datetime < now:
                free_object = models.PricePolicy.objects.filter(category=1).first()
                max_member = free_object.project_member
            else:
                max_member = max_transaction.price_policy.project_member
        if models.ProjectUser.objects.filter(project_id=invite_object.project_id).count() + 1 >= max_member:
            return render(request, 'invite_join.html', {'error': '项目人数已达最大'})
        if invite_object.create_datetime + datetime.timedelta(minutes=invite_object.period) < now:
            return render(request, 'invite_join.html', {'error': '邀请码已过期'})
        if invite_object.count:
            if invite_object.count <= invite_object.use_count:
                return render(request, 'invite_join.html', {'error': '此邀请码可邀请人数已达最大'})
            invite_object.use_count += 1
            invite_object.save()
        invite_object.project.join_count += 1
        invite_object.project.save()
        models.ProjectUser.objects.create(user=request.tracer, project=invite_object.project)
        return render(request, 'invite_join.html', {'invite_object': invite_object})
    return render(request, 'invite_join.html', {'error': '邀请码不存在'})

