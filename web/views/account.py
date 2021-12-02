import datetime
import uuid

from django.http import JsonResponse
from django.shortcuts import render, HttpResponse, redirect
from django.urls import reverse

from utils.tencent.sms import send_sms_single
from django.conf import settings
from web.forms.account import UserInfoModelForm, LoginForm, SmsLoginForm
from web import models
from utils.image_code import check_code
from io import BytesIO
import random


# Create your views here.


def send_sms(request):
    phone = request.POST.get('phone')
    tpl = request.POST.get('tpl')
    template_id = settings.TENCENT_SMS_TEMPLATE.get(tpl)
    user_object = models.UserInfo.objects.filter(mobile_phone=phone)
    if not template_id:
        return HttpResponse('模板不存在')
    if not user_object and tpl == 'register':
        return sms(phone, template_id)
    if tpl == 'login':
        if user_object:
            return sms(phone, template_id)
        return JsonResponse({'code': 1, 'msg': '此手机号不存在'})
    return JsonResponse({'code': 1, 'msg': '此手机号已存在'})


def register(request):
    if request.method == 'GET':
        form = UserInfoModelForm()
        return render(request, 'register.html', {'form': form})
    form = UserInfoModelForm(request.POST)
    if form.is_valid():
        instance = form.save()
        policy_object = models.PricePolicy.objects.filter(category='1').first()
        models.Transaction.objects.create(
            status=2,
            order=str(uuid.uuid4()),
            user=instance,
            price_policy=policy_object,
            count=0,
            price=0,
            start_datetime=datetime.datetime.now()
        )
        return JsonResponse({'code': 0, 'data': reverse('web:login')})
    return JsonResponse({'code': 1, 'msg': form.errors})


def login(request):
    if request.method == 'GET':
        form = LoginForm()
        return render(request, 'login.html', {'form': form})
    form = LoginForm(data=request.POST, request=request)
    if form.is_valid():
        request.session['user_id'] = form.cleaned_data.get('password').id
        request.session.set_expiry(60 * 60 * 24 * 14)
        return redirect(reverse('web:index'))
    return render(request, 'login.html', {'form': form})


def sms_login(request):
    if request.method == 'GET':
        form = SmsLoginForm()
        return render(request, 'sms_login.html', {'form': form})
    form = SmsLoginForm(request.POST)
    if form.is_valid():
        request.session['user_id'] = form.cleaned_data.get('password').id
        request.session.set_expiry(60 * 60 * 24 * 14)
        return JsonResponse({'code': 0, 'data': reverse('web:index')})
    return JsonResponse({'code': 2, 'msg': form.errors})


def image_code(request):
    image_object, code = check_code()
    stream = BytesIO()
    image_object.save(stream, 'png')
    request.session['image_code'] = code
    request.session.set_expiry(60)
    return HttpResponse(stream.getvalue())


def logout(request):
    request.session.flush()
    return redirect(reverse('web:index'))


def sms(phone, template_id):
    code = random.randrange(1000, 9999)
    settings.REDIS.set(phone, code, ex=60)
    res = send_sms_single(phone, template_id, [code, ])
    if res['result'] == 0:
        return JsonResponse({'code': 0, 'msg': ''})
    return JsonResponse({'code': 2, 'msg': res['errmsg']})
