from django.conf.urls import url
from web.views import account, home, project, statistics, wiki, file, setting, issues, dashboard

urlpatterns = [
    url(r'^send/sms/$', account.send_sms, name='code'),
    url(r'^register/$', account.register, name='register'),
    url(r'^login/sms/$', account.sms_login, name='sms_login'),
    url(r'^image/code/$', account.image_code, name='image_code'),
    url(r'^login/$', account.login, name='login'),
    url(r'^index/$', home.index, name='index'),
    url(r'^logout/$', account.logout, name='logout'),

    url(r'^price/$', home.price, name='price'),

    url(r'^pay/$', home.pay, name='pay'),
    url(r'^pay/notify/$', home.pay_notify, name='pay_notify'),
    url(r'^pay/order/list/$', home.order_list, name='order_list'),

    url(r'^payment/(?P<policy_id>\d+)/$', home.payment, name='payment'),

    # 项目列表
    url(r'^project/list/$', project.project_list, name='project_list'),
    url(r'^project/star/(?P<project_type>\w+)/(?P<project_id>\d+)/$', project.project_star, name='project_star'),
    url(r'^project/unstar/(?P<project_type>\w+)/(?P<project_id>\d+)/$', project.project_unstar, name='project_unstar'),


    url(r'^manage/(?P<project_id>\d+)/dashboard/$', dashboard.dashboard, name='dashboard'),
    url(r'^manage/(?P<project_id>\d+)/dashboard/issues/chart/$', dashboard.issues_chart, name='issues_chart'),

    url(r'^manage/(?P<project_id>\d+)/issues/$', issues.issues, name='issues'),
    url(r'^manage/(?P<project_id>\d+)/issues/detail/(?P<issues_id>\d+)/$', issues.issues_detail, name='issues_detail'),
    url(r'^manage/(?P<project_id>\d+)/issues/record/(?P<issues_id>\d+)/$', issues.issues_record, name='issues_record'),
    url(r'^manage/(?P<project_id>\d+)/issues/change/(?P<issues_id>\d+)/$', issues.issues_change, name='issues_change'),
    url(r'^manage/(?P<project_id>\d+)/invite/url/$', issues.invite_url, name='invite_url'),
    url(r'^invite/join/(?P<code>\w+)/$', issues.invite_join, name='invite_join'),

    url(r'^manage/(?P<project_id>\d+)/statistics/$', statistics.statistics, name='statistics'),
    url(r'^manage/(?P<project_id>\d+)/statistics/priority/$', statistics.statistics_priority, name='statistics_priority'),
    url(r'^manage/(?P<project_id>\d+)/statistics/project/user/$', statistics.statistics_project_user, name='statistics_project_user'),

    url(r'^manage/(?P<project_id>\d+)/file/$', file.file, name='file'),
    url(r'^manage/(?P<project_id>\d+)/file/delete/$', file.file_delete, name='file_delete'),
    url(r'^manage/(?P<project_id>\d+)/file/$', file.file, name='file'),
    url(r'^manage/(?P<project_id>\d+)/cos/credential/$', file.cos_credential, name='cos_credential'),
    url(r'^manage/(?P<project_id>\d+)/file/upload/$', file.file_upload, name='file_upload'),
    url(r'^manage/(?P<project_id>\d+)/file/download/$', file.file_download, name='file_download'),

    url(r'^manage/(?P<project_id>\d+)/wiki/$', wiki.wiki, name='wiki'),
    url(r'^manage/(?P<project_id>\d+)/wiki/add/$', wiki.wiki_add, name='wiki_add'),
    url(r'^manage/(?P<project_id>\d+)/wiki/delete/$', wiki.wiki_delete, name='wiki_delete'),
    url(r'^manage/(?P<project_id>\d+)/wiki/edit/$', wiki.wiki_edit, name='wiki_edit'),
    url(r'^manage/(?P<project_id>\d+)/wiki/upload/$', wiki.wiki_upload, name='wiki_upload'),

    url(r'^manage/catalog/(?P<project_id>\d+)/$', wiki.wiki_catalog, name='wiki_catalog'),

    url(r'^manage/(?P<project_id>\d+)/setting/$', setting.setting, name='setting'),
    url(r'^manage/(?P<project_id>\d+)/setting/delete/$', setting.delete, name='setting_delete'),


]
