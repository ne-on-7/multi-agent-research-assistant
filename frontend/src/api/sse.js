export async function streamQuery(query, onEvent, onDone, onError) {
  try {
    const response = await fetch('/api/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query }),
    });

    if (!response.ok) {
      throw new Error(`Server error: ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split('\n\n');
      buffer = parts.pop();

      for (const part of parts) {
        const line = part.trim();
        if (!line.startsWith('data: ')) continue;

        const payload = line.slice(6);
        if (payload === '[DONE]') {
          onDone();
          return;
        }

        try {
          onEvent(JSON.parse(payload));
        } catch (parseErr) {
          console.warn('[SSE] Malformed JSON payload:', payload, parseErr);
        }
      }
    }

    onDone();
  } catch (err) {
    onError(err);
  }
}
