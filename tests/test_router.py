from pipeline.routing.router import Router


class DummyToolService:
    def execute(self, intent_result, transcript: str, extra_text: str = "") -> dict:
        return {
            "action": intent_result.intent,
            "result": f"ok:{intent_result.intent}:{transcript}",
        }


class FailingToolService:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, _intent_result, _transcript: str, extra_text: str = "") -> dict:
        self.calls += 1
        raise RuntimeError("tool failure")


def test_router_maps_known_intent():
    router = Router(DummyToolService())
    payload = {"intent": "create_file", "filename": "generated/a.txt"}
    out = router.route(payload, "create file")

    assert out["action"] == "create_file"
    assert "ok:create_file" in out["result"]


def test_router_handles_unknown_intent_safely():
    router = Router(DummyToolService())
    payload = {"intent": "unknown_intent"}
    out = router.route(payload, "hello")

    assert out["action"] == "chat"
    assert "ok:general_chat" in out["result"]


def test_router_retries_and_returns_error():
    failing = FailingToolService()
    router = Router(failing)
    payload = {"intent": "write_code", "filename": "generated/x.py"}
    out = router.route(payload, "write code")

    assert "failed" in out["result"].lower()
    assert failing.calls == 3
