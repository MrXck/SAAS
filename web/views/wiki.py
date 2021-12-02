from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from utils.encrypt import uid
from utils.tencent.cos import upload_file
from web import models

from web.forms.wiki import WikiModelForm


def wiki(request, project_id):
    wiki_id = request.GET.get('wiki_id')
    if wiki_id:
        try:
            wiki_object = models.Wiki.objects.filter(id=int(wiki_id), project_id=project_id).first()
            return render(request, 'wiki.html', {'wiki_object': wiki_object})
        except:
            return redirect(reverse('web:wiki', kwargs={'project_id': project_id}))
    return render(request, 'wiki.html')


def wiki_add(request, project_id):
    if request.method == 'GET':
        form = WikiModelForm(request=request)
        return render(request, 'wiki_add.html', {'form': form})
    form = WikiModelForm(data=request.POST, request=request)
    if form.is_valid():
        form.instance.project = request.project
        form.save()
        return redirect(reverse('web:wiki', kwargs={'project_id': project_id}))
    return render(request, 'wiki_add.html', {'form': form})


def wiki_catalog(request, project_id):
    data = models.Wiki.objects.filter(project_id=project_id).values('id', 'title', 'parent_id')
    return JsonResponse({'data': list(data)})


def wiki_delete(request, project_id):
    wiki_id = request.GET.get('wiki_id')
    if wiki_id:
        try:
            models.Wiki.objects.filter(id=int(wiki_id), project_id=project_id).delete()
        except:
            pass
    return redirect(reverse('web:wiki', kwargs={'project_id': project_id}))


def wiki_edit(request, project_id):
    wiki_id = request.GET.get('wiki_id')
    try:
        data = models.Wiki.objects.filter(project_id=project_id, id=int(wiki_id)).first()
    except:
        return redirect(reverse('web:wiki', kwargs={'project_id': project_id}))
    if request.method == 'GET':
        if wiki_id:
            form = WikiModelForm(request=request, instance=data)
            return render(request, 'wiki_edit.html', {'form': form})
        return redirect(reverse('web:wiki', kwargs={'project_id': project_id}))
    form = WikiModelForm(data=request.POST, request=request, instance=data)
    if form.is_valid():
        form.instance.project = request.project
        form.save()
        return redirect(reverse('web:wiki', kwargs={'project_id': project_id}) + '?wiki_id=' + wiki_id)
    return render(request, 'wiki_edit.html', {'form': form})


@csrf_exempt
def wiki_upload(request, project_id):
    result = {'success': 0, 'message': None, 'url': None}
    image_object = request.FILES.get('editormd-image-file')
    if not image_object:
        result['message'] = '文件不存在'
        return JsonResponse(result)
    ext = image_object.name.rsplit('.')[-1]
    key = f'{uid(request.tracer.mobile_phone)}.{ext}'
    image_url = upload_file(request.project.bucket, request.project.region, image_object, key)
    result['success'] = 1
    result['url'] = image_url
    return JsonResponse(result)

