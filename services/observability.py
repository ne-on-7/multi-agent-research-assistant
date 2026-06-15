"""Langfuse tracing — thin, optional, and fail-safe (Langfuse Python SDK v4).

Tracing is enabled only when both Langfuse keys are set; otherwise every helper
here is a no-op and the app runs unchanged. Nesting is handled automatically by
the SDK's OpenTelemetry context — we just open a span around each unit of work,
and any generation created inside it attaches to the right parent.

Hierarchy produced per request:
    research_query (span)
      ├── retriever (agent)
      │     └── llm.generate (generation: model + token usage)
      ├── web_researcher (agent)
      │     └── llm.generate (generation)
      └── synthesizer (agent)
            └── llm.stream (generation, streamed)

The client is constructed explicitly from settings (not from os.environ) so it is
robust to how the .env is loaded, and so tracing initializes only after config is
available. All Langfuse calls are guarded — a tracing failure never breaks a
user request.
"""

import logging
from contextlib import contextmanager

from config.settings import settings

logger = logging.getLogger(__name__)

_client = None
_initialized = False


def get_langfuse():
    """Return a configured Langfuse client, or None when tracing is disabled."""
    global _client, _initialized
    if _initialized:
        return _client
    _initialized = True

    if not (settings.langfuse_public_key and settings.langfuse_secret_key):
        logger.info("Langfuse tracing disabled (set LANGFUSE_PUBLIC_KEY/SECRET_KEY to enable)")
        return None

    try:
        from langfuse import Langfuse

        _client = Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_base_url,
        )
        logger.info("Langfuse tracing enabled (host=%s)", settings.langfuse_base_url)
    except Exception as e:
        logger.warning("Failed to initialize Langfuse, tracing disabled: %s", e)
        _client = None
    return _client


@contextmanager
def start_trace(name: str, user_input: str = ""):
    """Open the root observation for one request. Yields an object with
    `.update(output=...)`; a no-op shim when tracing is disabled. Flushes on exit."""
    client = get_langfuse()
    cm = None
    if client is not None:
        try:
            cm = client.start_as_current_observation(as_type="span", name=name, input=user_input)
        except Exception as e:
            logger.warning("Langfuse start_trace setup failed: %s", e)
            cm = None

    if cm is None:
        yield _NullObservation()
        return

    try:
        with cm as root:
            yield root
    finally:
        try:
            client.flush()
        except Exception as e:
            logger.debug("Langfuse flush failed: %s", e)


@contextmanager
def traced_span(name: str, as_type: str = "agent"):
    """Open a child observation under the current one. No-op when tracing is off."""
    client = get_langfuse()
    cm = None
    if client is not None:
        try:
            cm = client.start_as_current_observation(as_type=as_type, name=name)
        except Exception as e:
            logger.debug("Langfuse traced_span(%s) setup failed: %s", name, e)
            cm = None

    if cm is None:
        yield None
        return
    with cm as span:
        yield span


@contextmanager
def trace_generation(name: str, model: str, prompt: str):
    """Open a generation observation around an LLM call. Yields the generation
    (or None when disabled); the caller sets `.update(output=..., usage_details=...)`."""
    client = get_langfuse()
    cm = None
    if client is not None:
        try:
            cm = client.start_as_current_observation(
                as_type="generation", name=name, model=model, input=prompt
            )
        except Exception as e:
            logger.debug("Langfuse trace_generation(%s) setup failed: %s", name, e)
            cm = None

    if cm is None:
        yield None
        return
    with cm as gen:
        yield gen


def shutdown():
    """Flush and stop the Langfuse background worker (call on app shutdown)."""
    client = get_langfuse()
    if client is None:
        return
    try:
        client.shutdown()
    except Exception as e:
        logger.debug("Langfuse shutdown failed: %s", e)


class _NullObservation:
    """Stand-in returned by start_trace when tracing is disabled."""

    def update(self, **kwargs):
        pass
