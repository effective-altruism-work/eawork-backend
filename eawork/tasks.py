from celery import shared_task
from celery.utils.log import get_task_logger


logger = get_task_logger(__name__)


@shared_task
def add(x, y):
    logger.info(f"Adding {x} + {y}")
    return x + y
