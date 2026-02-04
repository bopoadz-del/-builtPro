"""Backend shim for Slack webhook app."""

from __future__ import annotations

import importlib

from fastapi import FastAPI, Header, Request

slack_module = importlib.import_module("slack_webhook")

requests = slack_module.requests
log_alert = slack_module.log_alert
log_approval = slack_module.log_approval
APPROVAL_FILE = slack_module.APPROVAL_FILE


async def slack_interactivity(
    request: Request,
    x_slack_signature: str = Header(None),
    x_slack_request_timestamp: str = Header(None),
):
    slack_module.requests = requests
    slack_module.log_alert = log_alert
    slack_module.log_approval = log_approval
    slack_module.APPROVAL_FILE = APPROVAL_FILE
    return await slack_module.slack_interactivity(
        request,
        x_slack_signature=x_slack_signature,
        x_slack_request_timestamp=x_slack_request_timestamp,
    )


app = FastAPI()
app.add_api_route("/slack/interactivity", slack_interactivity, methods=["POST"])
