import os
import sys
import django


base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tracer.settings')
django.setup()

from web import models


if __name__ == '__main__':
    # obj = models.PricePolicy.objects.filter(category=1, title='个人免费版')

    models.PricePolicy.objects.create(
        category=2,
        title='VIP',
        price=100,
        project_num=50,
        project_member=10,
        project_space=10,
        per_file_size=500
    )

    models.PricePolicy.objects.create(
        category=2,
        title='SVIP',
        price=200,
        project_num=150,
        project_member=110,
        project_space=110,
        per_file_size=1024
    )

    models.PricePolicy.objects.create(
        category=2,
        title='SSVIP',
        price=500,
        project_num=550,
        project_member=510,
        project_space=510,
        per_file_size=2048
    )
