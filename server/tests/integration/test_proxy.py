"""V17 — Integration tests for the Zero-Code Memory Proxy.

Tests the full proxy pipeline: request normalization, memory injection,
forwarding, response extraction, and config management for all 3 providers.

Usage:
    cd server && uv run pytest tests/integration/test_proxy.py -v
"""

from fastapi.testclient import TestClient

from kyros.proxy.server import create_proxy_app
from kyros.proxy.architecture import ProxyConfig
from kyros.proxy.providers import OpenAIProvider, AnthropicProvider, GeminiProvider
from kyros.proxy.interceptors import (
    extract_agent_id,
    format_memory_block,
    should_store_response,
)
from kyros.proxy.classifier import (
    classify_content,
    extract_triples,
    MemoryCategory,
)


# ─── V06: Agent ID Extraction ─────────────────

class TestAgentIdExtraction:
    def test_extracts_standard_header(self):
        assert extract_agent_id({"X-Agent-ID": "my-agent"}) == "my-agent"

    def test_extracts_lowercase_header(self):
        assert extract_agent_id({"x-agent-id": "bot-42"}) == "bot-42"

    def test_returns_none_when_missing(self):
        assert extract_agent_id({"Content-Type": "application/json"}) is None

    def test_returns_none_for_empty_value(self):
        assert extract_agent_id({"X-Agent-ID": "  "}) is None


# ─── V03: OpenAI Provider ─────────────────────

class TestOpenAIProvider:
    def test_normalize_request_with_system(self):
        body = {
            "model": "gpt-4o",
            "messages": [
                {"role": "system", "content": "You are helpful."},
                {"role": "user", "content": "Hello!"},
            ],
        }
        result = OpenAIProvider.normalize_request(body, {})
        assert result.provider == "openai"
        assert result.model == "gpt-4o"
        assert result.system_message == "You are helpful."
        assert len(result.user_messages) == 1
        assert result.user_messages[0]["content"] == "Hello!"

    def test_normalize_request_without_system(self):
        body = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": "Hi"}],
        }
        result = OpenAIProvider.normalize_request(body, {})
        assert result.system_message == ""
        assert len(result.user_messages) == 1

    def test_inject_memories_with_existing_system(self):
        body = {
            "messages": [
                {"role": "system", "content": "Be concise."},
                {"role": "user", "content": "Hello"},
            ],
        }
        result = OpenAIProvider.inject_memories(body, "Be concise.", "MEMORY: user likes Python")
        system = next(m for m in result["messages"] if m["role"] == "system")
        assert "MEMORY: user likes Python" in system["content"]
        assert "Be concise." in system["content"]

    def test_inject_memories_without_system(self):
        body = {"messages": [{"role": "user", "content": "Hello"}]}
        result = OpenAIProvider.inject_memories(body, "", "MEMORY: test")
        assert result["messages"][0]["role"] == "system"
        assert "MEMORY: test" in result["messages"][0]["content"]

    def test_extract_response(self):
        body = {
            "choices": [{"message": {"role": "assistant", "content": "I am an AI."}}],
            "model": "gpt-4o",
        }
        result = OpenAIProvider.extract_response(200, body, {})
        assert result.assistant_content == "I am an AI."
        assert result.provider == "openai"


# ─── V04: Anthropic Provider ──────────────────

class TestAnthropicProvider:
    def test_normalize_request(self):
        body = {
            "model": "claude-3-5-sonnet-20241022",
            "system": "You are a poet.",
            "messages": [{"role": "user", "content": "Write a haiku."}],
        }
        result = AnthropicProvider.normalize_request(body, {})
        assert result.provider == "anthropic"
        assert result.system_message == "You are a poet."
        assert len(result.user_messages) == 1

    def test_inject_memories(self):
        body = {"system": "Be creative.", "messages": []}
        result = AnthropicProvider.inject_memories(body, "Be creative.", "MEMORY: likes haiku")
        assert "MEMORY: likes haiku" in result["system"]
        assert "Be creative." in result["system"]

    def test_extract_response(self):
        body = {"content": [{"type": "text", "text": "A lovely haiku."}], "model": "claude"}
        result = AnthropicProvider.extract_response(200, body, {})
        assert result.assistant_content == "A lovely haiku."


# ─── V05: Gemini Provider ─────────────────────

class TestGeminiProvider:
    def test_normalize_request(self):
        body = {
            "model": "gemini-1.5-flash",
            "systemInstruction": {"parts": [{"text": "Be helpful."}]},
            "contents": [{"role": "user", "parts": [{"text": "Hi"}]}],
        }
        result = GeminiProvider.normalize_request(body, {})
        assert result.provider == "gemini"
        assert "Be helpful." in result.system_message

    def test_inject_memories(self):
        body = {"systemInstruction": {"parts": [{"text": "Be factual."}]}, "contents": []}
        result = GeminiProvider.inject_memories(body, "Be factual.", "MEMORY: user is in London")
        text = result["systemInstruction"]["parts"][0]["text"]
        assert "MEMORY: user is in London" in text

    def test_extract_response(self):
        body = {"candidates": [{"content": {"parts": [{"text": "Gemini response."}]}}]}
        result = GeminiProvider.extract_response(200, body, {})
        assert result.assistant_content == "Gemini response."


# ─── V08: Memory Block Formatting ─────────────

class TestMemoryFormatting:
    def test_formats_memories_into_block(self):
        memories = [
            {"content": "User likes Python", "score": 0.9},
            {"content": "User works at TechCorp", "score": 0.8},
        ]
        template = "[Memories]\n{memories}\n[End]"
        result = format_memory_block(memories, template)
        assert "User likes Python" in result
        assert "User works at TechCorp" in result
        assert "[Memories]" in result

    def test_empty_memories_returns_empty(self):
        assert format_memory_block([], "template {memories}") == ""


# ─── V09: Response Filtering ──────────────────

class TestResponseFiltering:
    def setup_method(self):
        self.config = ProxyConfig()

    def test_stores_meaningful_response(self):
        assert should_store_response(
            "The user prefers dark mode and Python for all backend work.", self.config
        )

    def test_skips_trivial_response(self):
        assert not should_store_response("Hello!", self.config)
        assert not should_store_response("Sure.", self.config)
        assert not should_store_response("Ok", self.config)

    def test_skips_empty(self):
        assert not should_store_response("", self.config)
        assert not should_store_response("   ", self.config)

    def test_skips_very_short(self):
        assert not should_store_response("Yes no", self.config)


# ─── V10: Classifier ──────────────────────────

class TestClassifier:
    def test_classifies_semantic(self):
        result = classify_content("Alice works at TechCorp as an engineer. She lives in London.")
        assert result.category == MemoryCategory.SEMANTIC

    def test_classifies_procedural(self):
        result = classify_content(
            "Step 1: Install dependencies. Then run the build command. Next deploy to production."
        )
        assert result.category == MemoryCategory.PROCEDURAL

    def test_classifies_skip(self):
        result = classify_content("Hello!")
        assert result.category == MemoryCategory.SKIP

    def test_classifies_episodic_default(self):
        result = classify_content(
            "Today we discussed the quarterly revenue targets and the team agreed on the timeline."
        )
        assert result.category == MemoryCategory.EPISODIC

    def test_importance_boosted_by_keywords(self):
        result = classify_content("CRITICAL: The password for the production database is needed urgently.")
        assert result.importance > 0.7


# ─── V12: Triple Extraction ───────────────────

class TestTripleExtraction:
    def test_extracts_works_at(self):
        triples = extract_triples("Alice works at TechCorp.")
        assert len(triples) >= 1
        assert triples[0].subject == "Alice"
        assert triples[0].predicate == "works_at"
        assert "TechCorp" in triples[0].obj

    def test_extracts_lives_in(self):
        triples = extract_triples("Bob lives in London.")
        assert len(triples) >= 1
        assert triples[0].predicate == "lives_in"

    def test_extracts_preference(self):
        triples = extract_triples("Charlie prefers TypeScript.")
        assert len(triples) >= 1
        assert triples[0].predicate == "prefers"

    def test_no_triples_in_generic_text(self):
        triples = extract_triples("The weather is nice today and I feel great about it.")
        assert len(triples) == 0


# ─── V16: Runtime Config ──────────────────────

class TestProxyConfig:
    def setup_method(self, method: object) -> None:
        import os

        self._prev_admin_token = os.environ.get("KYROS_PROXY_ADMIN_TOKEN")
        os.environ["KYROS_PROXY_ADMIN_TOKEN"] = "proxy-admin-token"
        config = ProxyConfig(kyros_api_key="test-key")
        self.app = create_proxy_app(config)
        self.client = TestClient(self.app)
        self.admin_headers = {"X-Proxy-Admin-Token": "proxy-admin-token"}

    def teardown_method(self, method: object) -> None:
        import os

        if self._prev_admin_token is None:
            os.environ.pop("KYROS_PROXY_ADMIN_TOKEN", None)
        else:
            os.environ["KYROS_PROXY_ADMIN_TOKEN"] = self._prev_admin_token

    def test_health_check(self) -> None:
        resp = self.client.get("/proxy/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_get_config(self) -> None:
        resp = self.client.get("/proxy/config", headers=self.admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "injection_enabled" in data
        assert "extraction_enabled" in data
        assert "extraction_sensitivity" in data

    def test_update_config_toggle_injection(self) -> None:
        resp = self.client.put(
            "/proxy/config",
            json={"injection_enabled": False},
            headers=self.admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "injection_enabled" in data["updated"]
        assert data["config"]["injection_enabled"] is False

    def test_update_config_sensitivity(self) -> None:
        resp = self.client.put(
            "/proxy/config",
            json={"extraction_sensitivity": 0.8},
            headers=self.admin_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["config"]["extraction_sensitivity"] == 0.8

    def test_update_config_clamps_values(self) -> None:
        resp = self.client.put(
            "/proxy/config",
            json={"extraction_sensitivity": 5.0},
            headers=self.admin_headers,
        )
        assert resp.json()["config"]["extraction_sensitivity"] == 1.0

        resp = self.client.put(
            "/proxy/config",
            json={"max_memories_to_inject": 100},
            headers=self.admin_headers,
        )
        assert resp.json()["config"]["max_memories_to_inject"] == 20

    def test_config_requires_admin_token(self) -> None:
        resp = self.client.get("/proxy/config")
        assert resp.status_code == 401

    def test_metrics_endpoint(self) -> None:
        resp = self.client.get("/proxy/metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert "requests_total" in data
        assert "memories_injected" in data
