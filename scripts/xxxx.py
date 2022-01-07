import os
import sys
import django


base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tracer.settings')
django.setup()

from web import models

from utils.tencent.cos import check_file


check_file('17607007993-1637381349202-1308249213', 'ap-chengdu', "" + '45f157355d4cb21dd79e5b1c0c62fa83' + "")