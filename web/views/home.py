import datetime
import json
import time
from urllib.parse import quote_plus, parse_qs

from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.conf import settings

from utils.alipay import AliPay
from utils.encrypt import uid
from web import models
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256
from base64 import encodebytes


def index(request):
    return render(request, 'index.html')


def price(request):
    policy_list = models.PricePolicy.objects.filter(category=2)

    return render(request, 'price.html', {'policy_list': policy_list})


def payment(request, policy_id):
    number = request.GET.get('number', '')
    policy_object = models.PricePolicy.objects.filter(id=policy_id, category=2).first()
    if not policy_object or not number or not number.isdecimal():
        return redirect(reverse('web:price'))
    number = int(number)
    if number < 1:
        return redirect(reverse('web:price'))
    origin_price = policy_object.price * number
    balance = 0
    _object = None
    if request.price_policy.category == 2:
        _object = models.Transaction.objects.filter(user=request.tracer, status=2).order_by('-id').first()
        total_timedelta = _object.end_datetime - _object.start_datetime
        balance_timedelta = _object.end_datetime - datetime.datetime.now()
        balance = _object.price / total_timedelta.days * balance_timedelta.days
    if balance >= origin_price:
        return redirect(reverse('web:price'))
    conn = settings.REDIS
    context = {
        'policy_id': policy_object.id,
        'number': number,
        'origin_price': origin_price,
        'balance': round(balance, 2),
        'total_price': origin_price - round(balance, 2),
    }
    conn.set(f'payment_{request.tracer.mobile_phone}', json.dumps(context), ex=60 * 30)
    context['policy_object'] = policy_object
    context['transaction'] = _object
    return render(request, 'payment.html', context)


# def pay(request):
#     context = settings.REDIS.get(f'payment_{request.tracer.mobile_phone}')
#     if not context:
#         return redirect(reverse('web:price'))
#     context = json.loads(context.decode('utf-8'))
#     order = uid(request.tracer.mobile_phone)
#     models.Transaction.objects.create(
#         status=1,
#         user=request.tracer,
#         order=order,
#         price_policy_id=context['policy_id'],
#         count=context['number'],
#         price=context['total_price'],
#     )
#     gateway = 'https://openapi.alipaydev.com/gateway.do'
#     params = {
#         'app_id': "2021000118658349",
#         'method': "alipay.trade.page.pay",
#         'format': "JSON",
#         'return_url': "http://127.0.0.1:8000/pay/notify",
#         'notify_url': "http://127.0.0.1:8000/pay/notify",
#         'charset': "utf-8",
#         'sign_type': "RSA2",
#         'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
#         'version': "1.0",
#         'biz_content': json.dumps({
#             'out_trade_no': order,
#             'product_code': 'FAST_INSTANT_TRADE_PAY',
#             'total_amount': context['total_price'],
#             'subject': 'tracer payment',
#         }, separators=(',', ':')),
#     }
#     unsigned_string = "&".join([f"{k}={params[k]}" for k in sorted(params)])
#
#     private_key = RSA.importKey(open('files/应用私钥_RSA2_PKCS1.txt').read())
#     signer = PKCS1_v1_5.new(private_key)
#     signature = signer.sign(SHA256.new(unsigned_string.encode('utf-8')))
#
#     sing_string = encodebytes(signature).decode('utf-8').replace('\n', '')
#
#     result = '&'.join([f"{k}={quote_plus(params[k])}" for k in sorted(params)])
#     result = result + f'&sign={quote_plus(sing_string)}'
#     pay_url = f'{gateway}?{result}'
#     return redirect(pay_url)

def pay(request):
    context = settings.REDIS.get(f'payment_{request.tracer.mobile_phone}')
    if not context:
        return redirect(reverse('web:price'))
    context = json.loads(context.decode('utf-8'))
    order = uid(request.tracer.mobile_phone)
    models.Transaction.objects.create(
        status=1,
        user=request.tracer,
        order=order,
        price_policy_id=context['policy_id'],
        count=context['number'],
        price=context['total_price'],
    )
    gateway = settings.ALI_GATEWAY
    alipay = AliPay(
        appid=settings.ALIPAY_APPID,
        app_notify_url=settings.ALI_NOTIFY_URL,
        return_url=settings.ALI_RETURN_URL,
        app_private_key_path=settings.ALI_PRI_KEY_PATH,
        alipay_public_key_path=settings.ALI_PUB_KEY_PATH,
    )
    query_params = alipay.direct_pay(
        subject='Tracer payment',
        out_trade_no=order,
        total_amount=context['total_price'],
    )
    pay_url = f'{gateway}?{query_params}'
    return redirect(pay_url)


def pay_notify(request):
    alipay = AliPay(
        appid=settings.ALIPAY_APPID,
        app_notify_url=settings.ALI_NOTIFY_URL,
        return_url=settings.ALI_RETURN_URL,
        app_private_key_path=settings.ALI_PRI_KEY_PATH,
        alipay_public_key_path=settings.ALI_PUB_KEY_PATH,
    )
    if request.method == 'GET':
        params = request.GET.dict()
        sign = params.pop('sign', None)
        status = alipay.verify(params, sign)
        if status:
            return HttpResponse('支付成功')
        return HttpResponse('支付失败')
    body_str = request.body.decode('utf-8')
    post_data = parse_qs(body_str)
    post_dict = {}
    for k, v in post_data.items():
        post_dict[k] = v[0]
    sign = post_dict.pop('sign', None)
    status = alipay.verify(post_dict, sign)
    if status:
        current_datetime = datetime.datetime.now()
        out_trade_no = post_dict['out_trade_no']
        _object = models.Transaction.objects.filter(order=out_trade_no).fitst()
        _object.status = 2
        _object.start_datetime = current_datetime
        _object.end_datetime = current_datetime + datetime.timedelta(days=365 * _object.count)
        _object.save()
        return HttpResponse('success')
    return HttpResponse('')


def order_list(request):
    transaction_object = models.Transaction.objects.filter(status=1, user=request.tracer).order_by('-id').first()
    now = time.time()
    create_datetime = time.mktime(time.strptime(str(transaction_object.create_datetime.strftime('%Y-%m-%d %H:%M:%S')), '%Y-%m-%d %H:%M:%S'))
    if create_datetime + 30 * 60 < now:
        return render(request, 'order_list.html')
    return render(request, 'order_list.html', {'transaction_object': transaction_object})
