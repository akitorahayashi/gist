import logging
import os

from celery import Celery

# DjangoのsettingsモジュールをCeleryに設定
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("config")

# DjangoのsettingsオブジェクトからCeleryの設定を読み込む
# namespace='CELERY'は、settings.py内のCelery設定がCELERY_から始まることを示す
app.config_from_object("django.conf:settings", namespace="CELERY")

# Djangoアプリケーションのtasks.pyファイルを自動的に検出
app.autodiscover_tasks()


logger = logging.getLogger(__name__)


@app.task(bind=True)
def debug_task(self):
    logger.debug("Request: %r", self.request)
