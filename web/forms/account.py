from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.conf import settings

from web import models
from utils import encrypt
from django.core.validators import RegexValidator


class UserInfoModelForm(forms.ModelForm):
    password = forms.CharField(label='密码', widget=forms.PasswordInput(), min_length=6,
                               error_messages={
                                   'min_length': '密码长度不能小于6',
                                   'max_length': '密码长度不能大于32',
                               }, max_length=32)
    confirm_password = forms.CharField(label='重复密码', widget=forms.PasswordInput())
    code = forms.CharField(label='验证码')
    mobile_phone = forms.CharField(label='手机号', validators=[RegexValidator(r'^1[0-9]{10}$', '请输入正确的手机号')])

    class Meta:
        model = models.UserInfo
        fields = ['username', 'password', 'confirm_password', 'email', 'mobile_phone', 'code']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = f'请输入{field.label}'

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if models.UserInfo.objects.filter(username=username):
            raise ValidationError('用户名已存在')
        return username

    def clean_confirm_password(self):
        password = self.cleaned_data.get('password')
        confirm_password = encrypt.md5(self.cleaned_data.get('confirm_password'))
        if password != confirm_password:
            raise ValidationError('此项与密码不一致')
        return confirm_password

    def clean_password(self):
        password = self.cleaned_data.get('password')
        return encrypt.md5(password)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if models.UserInfo.objects.filter(email=email):
            raise ValidationError('邮箱已存在')
        return email

    def clean_mobile_phone(self):
        mobile_phone = self.cleaned_data.get('mobile_phone')
        if models.UserInfo.objects.filter(mobile_phone=mobile_phone):
            raise ValidationError('手机号已存在')
        return mobile_phone

    def clean_code(self):
        mobile_phone = self.cleaned_data.get('mobile_phone')
        code = self.cleaned_data.get('code').strip()
        result = settings.REDIS.get(mobile_phone)
        if not result:
            raise ValidationError('验证码不存在')
        if result.decode('utf-8') != code:
            raise ValidationError('验证码错误')
        return code


class LoginForm(forms.Form):
    username = forms.CharField(label='用户名', required=True)
    password = forms.CharField(label='密码', widget=forms.PasswordInput(), required=True)
    code = forms.CharField(label='图片验证码', required=True)

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name == 'username':
                field.widget.attrs['class'] = 'form-control'
                field.widget.attrs['placeholder'] = f'请输入手机号或者邮箱'
            else:
                field.widget.attrs['class'] = 'form-control'
                field.widget.attrs['placeholder'] = f'请输入{field.label}'

    def clean_password(self):
        username = self.cleaned_data.get('username')
        password = encrypt.md5(self.cleaned_data.get('password'))
        user_object = models.UserInfo.objects.filter(Q(Q(mobile_phone=username) | Q(email=username)) & Q(password=password)).first()
        if not user_object:
            raise ValidationError('用户名不存在或密码错误')
        return user_object

    def clean_code(self):
        code = self.cleaned_data.get('code')
        session_code = self.request.session.get('image_code')
        if not session_code:
            raise ValidationError('验证码已过期')
        if code.strip().upper() != session_code.strip().upper():
            raise ValidationError('验证码错误')
        return code


class SmsLoginForm(forms.Form):
    mobile_phone = forms.CharField(label='手机号', required=True)
    code = forms.CharField(label='验证码', required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = f'请输入{field.label}'

    def clean_code(self):
        mobile_phone = self.cleaned_data.get('mobile_phone')
        code = self.cleaned_data.get('code').strip()
        result = settings.REDIS.get(mobile_phone)
        if not result:
            raise ValidationError('验证码不存在')
        if result.decode('utf-8') != code:
            raise ValidationError('验证码错误')
        return code

    def clean_mobile_phone(self):
        mobile_phone = self.cleaned_data.get('mobile_phone').mobile_phone
        user_object = models.UserInfo.objects.filter(mobile_phone=mobile_phone).first()
        if not user_object:
            raise ValidationError('手机号不存在')
        return user_object
