import pytest

from kb_bot.services import embedding_providers as providers_module
from kb_bot.services.embedding_providers import LocalHTTPEmbeddingProvider


class _FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, object]:
        return self._payload


class _FakeAsyncClient:
    def __init__(self, *, timeout: float, payload: dict[str, object], capture: dict[str, object]) -> None:
        self.timeout = timeout
        self._payload = payload
        self._capture = capture

    async def __aenter__(self) -> "_FakeAsyncClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    async def post(self, url: str, json: dict[str, object], headers: dict[str, object] | None = None) -> _FakeResponse:
        self._capture["url"] = url
        self._capture["json"] = json
        self._capture["headers"] = headers
        return _FakeResponse(self._payload)


@pytest.mark.asyncio
async def test_local_provider_sends_prompt_for_ollama_api(monkeypatch: pytest.MonkeyPatch) -> None:
    capture: dict[str, object] = {}
    fake_payload = {"embedding": [0.1, 0.2, 0.3]}

    def _factory(*, timeout: float, trust_env: bool) -> _FakeAsyncClient:
        assert trust_env is False
        return _FakeAsyncClient(timeout=timeout, payload=fake_payload, capture=capture)

    monkeypatch.setattr(providers_module.httpx, "AsyncClient", _factory)

    provider = LocalHTTPEmbeddingProvider(
        url="http://127.0.0.1:11434/api/embeddings",
        model="nomic-embed-text",
        timeout_ms=5000,
    )
    vector = await provider.embed("test payload")

    assert vector == [0.1, 0.2, 0.3]
    assert capture["url"] == "http://127.0.0.1:11434/api/embeddings"
    assert capture["json"] == {"model": "nomic-embed-text", "prompt": "test payload"}


@pytest.mark.asyncio
async def test_local_provider_rejects_empty_embedding_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    capture: dict[str, object] = {}
    fake_payload = {"embedding": []}

    def _factory(*, timeout: float, trust_env: bool) -> _FakeAsyncClient:
        assert trust_env is False
        return _FakeAsyncClient(timeout=timeout, payload=fake_payload, capture=capture)

    monkeypatch.setattr(providers_module.httpx, "AsyncClient", _factory)

    provider = LocalHTTPEmbeddingProvider(
        url="http://127.0.0.1:11434/api/embeddings",
        model="nomic-embed-text",
        timeout_ms=5000,
    )

    with pytest.raises(RuntimeError, match="unsupported response shape"):
        await provider.embed("test payload")


@pytest.mark.asyncio
async def test_local_provider_sends_input_for_openai_compatible_endpoint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    capture: dict[str, object] = {}
    fake_payload = {"embedding": [0.5]}

    def _factory(*, timeout: float, trust_env: bool) -> _FakeAsyncClient:
        assert trust_env is False
        return _FakeAsyncClient(timeout=timeout, payload=fake_payload, capture=capture)

    monkeypatch.setattr(providers_module.httpx, "AsyncClient", _factory)

    provider = LocalHTTPEmbeddingProvider(
        url="http://127.0.0.1:8080/v1/embeddings",
        model="local-openai-compatible",
        timeout_ms=5000,
    )
    vector = await provider.embed("another payload")

    assert vector == [0.5]
    assert capture["json"] == {"model": "local-openai-compatible", "input": "another payload"}
