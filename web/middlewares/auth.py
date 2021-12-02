import datetime

from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect
from django.conf import settings
from web import models


class AuthMiddleware(MiddlewareMixin):

    def process_request(self, request):
        user_id = request.session.get('user_id')
        user_object = models.UserInfo.objects.filter(id=user_id).first()
        request.tracer = user_object
        request.project = None

        if request.path_info in settings.WHITE_REGEX_URL_LIST:
            return
        if not request.tracer:
            return redirect(reverse('web:login'))

        _object = models.Transaction.objects.filter(user=user_object, status=2).order_by('-id').first()
        current_datetime = datetime.datetime.now()
        if _object.end_datetime and _object.end_datetime < current_datetime:
            _object = models.Transaction.objects.filter(user=user_object, status=2, price_policy__category=1).first()
        request.transaction = _object
        request.price_policy = _object.price_policy

    def process_view(self, request, view, args, kwargs):
        if not request.path_info.startswith('/manage/'):
            return
        project_id = kwargs.get('project_id')
        user = request.tracer
        my_project = models.Project.objects.filter(creator=user, id=project_id).first()
        if my_project:
            request.project = my_project
            return
        join_project = models.ProjectUser.objects.filter(user=user, project_id=project_id).first()
        if join_project:
            request.project = join_project.project
            return
        return redirect(reverse('web:project_list'))
