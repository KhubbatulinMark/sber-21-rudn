import logging

import requests
from airflow.models import Variable

log = logging.getLogger(__name__)


def _send(text: str) -> None:
    try:
        token = Variable.get("tg_token", default_var=None)
        chat_id = Variable.get("tg_chat_id", default_var=None)
    except Exception:
        token = chat_id = None
    if not token or not chat_id:
        log.warning("telegram alert skipped: tg_token / tg_chat_id not set\n%s", text)
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
            timeout=10,
        )
    except requests.RequestException as exc:
        log.error("telegram alert failed: %s", exc)


def notify_failure(context: dict) -> None:
    ti = context["task_instance"]
    text = (
        f"❌ DAG <b>{ti.dag_id}</b> / task <b>{ti.task_id}</b> failed\n"
        f"run: {context['run_id']}\n"
        f"log: {ti.log_url}"
    )
    _send(text)


def notify_text(text: str) -> None:
    _send(text)
