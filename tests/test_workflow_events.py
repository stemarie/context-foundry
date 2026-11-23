import http.server
import threading
import unittest

from foundry_runtime.events import workflow_events
from foundry_runtime.runtime import Client, ServiceError, ServiceUnavailable


PROJECT = "00000000-0000-4000-8000-000000000001"


class WorkflowEventsTest(unittest.TestCase):
    def setUp(self):
        self.frames = b"event: subscribed\ndata: {}\n\n: keepalive\n\nevent: workflow_changed\ndata: {}\n\n"
        self.requests = []
        test = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                auth = self.headers.get("Authorization")
                test.requests.append((self.path, auth))
                if auth != "Bearer reader":
                    self.send_error(401)
                    return
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.end_headers()
                self.wfile.write(test.frames)

        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01})
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join)
        self.addCleanup(server.shutdown)
        self.origin = f"http://127.0.0.1:{server.server_port}"

    def test_reconnect_starts_new_subscription(self):
        for _ in range(2):
            with workflow_events(Client(self.origin, "reader"), PROJECT) as events:
                self.assertIsNone(next(events))
                with self.assertRaises(ServiceUnavailable):
                    next(events)
        self.assertEqual(self.requests, [
            (f"/api/v1/workflow/stream?project_id={PROJECT}", "Bearer reader"),
        ] * 2)

    def test_authentication_failure(self):
        with self.assertRaises(ServiceError):
            with workflow_events(Client(self.origin, "wrong"), PROJECT):
                self.fail("authenticated unexpectedly")

    def test_acknowledgement_required(self):
        self.frames = b"event: workflow_changed\ndata: {}\n\n"
        with self.assertRaises(ServiceError):
            with workflow_events(Client(self.origin, "reader"), PROJECT):
                self.fail("confirmed subscription without acknowledgement")
