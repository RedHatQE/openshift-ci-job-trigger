import json

import requests


def send_slack_message(message, webhook_url, log_prefix, app_logger):
    slack_data = {"text": message}
    app_logger.info(f"{log_prefix} Sending message to slack: {message}")
    response = requests.post(webhook_url, data=json.dumps(slack_data), headers={"Content-Type": "application/json"})
    if response.status_code != 200:
        raise ValueError(
            f"Request to slack returned an error {response.status_code} with the following message: " f"{response.text}"
        )
