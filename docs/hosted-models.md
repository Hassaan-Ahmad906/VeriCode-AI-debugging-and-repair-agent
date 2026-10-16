# Your own API connection

Open **Models & API** → enter a key → **Verify key & fetch models** → choose a
model → set a positive total USD limit → authorize → **Connect model**. The
connected provider is selected in Repair workbench. Each browser session manages
its own connection; disconnect before sharing a browser. Never put a key in chat,
Git, a task or a source file.

Supported connections are OpenAI and OpenRouter, alongside free local Ollama and
the scripted demonstration. OpenRouter makes other providers' models available
through that account; direct Anthropic/Gemini/Groq adapters are not implemented.
The CLI's historical study/batch commands remain scripted-only. Hosted repair
currently uses the UI or an explicit in-process `HostedConnection` context.

Verification authenticates with model/key metadata GET requests and fetches
official prices; it performs no inference. A successful metadata check confirms
catalog access, not every model's chat compatibility, credits or quota. Unsupported
models can still be rejected at inference. OpenAI models are intersected with the
official standard pricing table; specialized audio/image/search models are omitted.
OpenRouter requires text output, JSON responses, output limits and token-only
prices. No unknown price is invented. Re-verify after pricing expires (24 hours).

API keys live only in server-session memory and the HTTPS Authorization header.
No global environment variables or provider clients are shared between users.
Context-local connections prevent a concurrent session from inheriting another
session's credential. Candidate containers receive neither keys nor socket access.
Exports contain provider/model, calls, tokens, fetched rates/source/time and budget
state, not credentials or credential hashes. The controller bypasses system HTTP
proxies, accepts only official allowlisted HTTPS hosts and follows no redirects.

## Usage and limits

- OpenAI returns prompt/completion tokens. USD cost is a **standard-rate estimate**
  calculated from its fetched official prices; cache discounts are not applied.
- OpenRouter's USD `usage.cost` is provider-reported. Its catalog rates set route
  price caps; fallback routes are disabled. Missing cost blocks further calls.
- Usage & cost links to the provider activity/billing dashboard. An ordinary
  project key does not grant organization-admin billing access. This application
  does not claim to retrieve an OpenAI invoice or account-wide spending.
- Local API cost is zero; local compute and GPU training are separate. Missing
  usage remains unknown. There are no automatic paid transport retries.

Before each HTTP inference, an SQLite transaction reserves an upper token-rate
allowance against that credential's cumulative cap. OpenAI uses UTF-8 prompt bytes
plus framing headroom; OpenRouter reserves its entire advertised context because
model tokenizers differ. This can require substantially more available budget than
the eventual cost. Bounds are checked again against the response. Unknown outcomes
retain their reservation and block that key across app restarts. Concurrent calls
with the same key cannot both obtain a reservation. Reconnection never clears
earlier spend. Do not delete `artifacts/private/usage.sqlite3` to evade a cap.

This is application-side accounting, not a provider-enforced invoice guarantee.
Provider pricing changes, additional account charges or use outside this app are
outside the ledger. Configure limits with the provider as well. If a request times
out, compare provider activity and reconcile with the operator before more calls;
there is no automatic refund/reset button.

No real paid request or real-key verification was performed during implementation.
Integration checks use simulated HTTP responses; connect your own account to
verify actual model access. The original frozen research evidence is unchanged.

Official sources: [OpenAI pricing](https://developers.openai.com/api/docs/pricing),
[Chat completions](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create),
[OpenAI models](https://developers.openai.com/api/reference/resources/models/methods/list),
[OpenRouter catalog](https://openrouter.ai/docs/api/api-reference/models/list-all-models-and-their-properties),
[OpenRouter key verification](https://openrouter.ai/docs/api/api-reference/api-keys/get-current-api-key),
[OpenRouter routing](https://openrouter.ai/docs/guides/routing/provider-selection).
