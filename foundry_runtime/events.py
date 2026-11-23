"""Consume AI.Contract workflow wake-ups. Durable workflow state lives in the API."""

import contextlib
import http.client
import urllib.error
import urllib.parse
import urllib.request
import uuid

from .core import Barrier
from .runtime import ServiceError, ServiceUnavailable


@contextlib.contextmanager
def workflow_events(client, project_id, timeout=45):
    """Yield wake-ups after the subscription is active.

    Reconcile current state on entering the context and after each wake-up.
    A disconnect ends this subscription and requires a fresh reconciliation.
    """
    try:
        if str(uuid.UUID(project_id)) != project_id:
            raise ValueError
    except (AttributeError, TypeError, ValueError):
        raise Barrier("expected a canonical project UUID") from None
    query = urllib.parse.urlencode({"project_id": project_id})
    request = urllib.request.Request(
        client.origin + "/api/v1/workflow/stream?" + query,
        headers={"Authorization": "Bearer " + client.token, "Accept": "text/event-stream"},
    )
    try:
        response = client.opener.open(request, timeout=timeout)
    except urllib.error.HTTPError as exc:
        exc.close()
        if exc.code in (401, 403, 404):
            raise ServiceError("workflow_stream_http_" + str(exc.code)) from None
        raise ServiceUnavailable("workflow_stream_http_" + str(exc.code)) from None
    except (OSError, http.client.HTTPException):
        raise ServiceUnavailable("workflow_stream_disconnected") from None

    with response:
        if response.headers.get_content_type() != "text/event-stream":
            raise ServiceError("unexpected_workflow_stream_content_type")
        events = _frames(response)
        if next(events) != b"subscribed":
            raise ServiceError("missing_workflow_subscription_acknowledgement")
        yield (None for event in events if event == b"workflow_changed")


def _frames(stream):
    event = None
    while True:
        try:
            line = stream.readline(4097)
        except (OSError, http.client.HTTPException):
            raise ServiceUnavailable("workflow_stream_disconnected") from None
        if not line:
            raise ServiceUnavailable("workflow_stream_disconnected")
        if len(line) > 4096 or not line.endswith(b"\n"):
            raise ServiceError("invalid_workflow_stream_frame")
        line = line.rstrip(b"\r\n")
        if not line:
            if event:
                yield event
            event = None
        elif line.startswith(b"event: "):
            event = line[7:]
