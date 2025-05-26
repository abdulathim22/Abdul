import os
import sys

# إضافة مسار المشروع إلى مسارات النظام
path = os.path.dirname(os.path.abspath(__file__))
if path not in sys.path:
    sys.path.append(path)

# تعيين متغيرات البيئة
os.environ['FLASK_ENV'] = 'production'
os.environ['SECRET_KEY'] = 'your-secret-key-here'
os.environ['FLASK_APP'] = 'src.main'

# استيراد تطبيق Flask
from src.main import app as application

# تطبيق PythonAnywhere يتوقع متغير application
application.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')
