import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# للإنتاج (مثل Render) عيّن SECRET_KEY و FLASK_DEBUG في لوحة التحكم أو عبر render.yaml
SECRET_KEY = os.environ.get('SECRET_KEY', 'smart-stadium-dev-only-change-in-production')
DATABASE_PATH = os.environ.get(
    'DATABASE_PATH', os.path.join(BASE_DIR, 'data', 'stadium.db')
)
_flask_debug = os.environ.get('FLASK_DEBUG')
if _flask_debug is None:
    DEBUG = True  # سلوك التطوير المحلي الافتراضي
else:
    DEBUG = _flask_debug.lower() in ('1', 'true', 'yes')
