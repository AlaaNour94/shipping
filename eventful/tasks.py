import logging
import requests

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def notify(webhook, event, payload, headers):
    """
    notifies webhook by sending it POST request.
    playload sent by caller.
    func is celery task to allow async operation.
    :type webhook: string
    :type event: string
    :type payload: dict
    """
    try:
        response = requests.request(
            'POST',
            webhook,
            json={
                "event": event,
                "payload": payload
            },
            headers=headers,
        )
        response.raise_for_status()
    except requests.exceptions.HTTPError as error:
        logger.exception(f"Error {error} while sending http request to url {webhook} with payload {payload} with headers {headers} for event {event}") # noqa
