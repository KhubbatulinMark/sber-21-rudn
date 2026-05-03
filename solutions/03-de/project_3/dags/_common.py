from datetime import timedelta

from include.alerts.telegram import notify_failure

DEFAULT_ARGS = {
    "owner": "olist",
    "retries": 3,
    "retry_delay": timedelta(minutes=1),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(minutes=10),
    "execution_timeout": timedelta(minutes=30),
    "on_failure_callback": notify_failure,
}
