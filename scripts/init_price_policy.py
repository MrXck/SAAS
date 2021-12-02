import os
import sys
import django


base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tracer.settings')
django.setup()

from web import models


if __name__ == '__main__':
    obj = models.PricePolicy.objects.filter(category=1, title='个人免费版')

    if not obj:
        models.PricePolicy.objects.create(
            category=1,
            title='个人免费版',
            price=0,
            project_num=3,
            project_member=2,
            project_space=20,
            per_file_size=5
        )
