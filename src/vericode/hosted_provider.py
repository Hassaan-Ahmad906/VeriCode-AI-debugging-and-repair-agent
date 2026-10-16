"""User-owned hosted connections, official pricing and durable spending reservations.

No key is serialized. A connection must be verified and explicitly funded before
generation; metadata verification never requests an inference. Unknown billed
outcomes block that credential's ledger rather than silently refunding a call.
"""

from contextlib import contextmanager, closing
from contextvars import ContextVar
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_CEILING
import hashlib
import http.client
import json
import math
from pathlib import Path
import sqlite3
import time
from uuid import uuid4

from vericode.checkpoints import decode_json
from vericode.model_calls import RawCompletion, StructuredProvider, TransportError
from vericode.model_io import Usage
from vericode.schemas import ValidationError

PROVIDERS = {"openai": ("api.openai.com", "/v1"), "openrouter": ("openrouter.ai", "/api/v1")}
PRICING_URL = "https://developers.openai.com/api/docs/pricing"
_CONNECTION = ContextVar("vericode_hosted_connection", default=None)
NANO = 1_000_000_000


def request_bytes(host, path, *, key=None, payload=None, timeout=15, limit=262144):
    if host not in {"api.openai.com", "openrouter.ai", "developers.openai.com"}:
        raise TransportError("Unapproved provider host")
    if key is not None and (not isinstance(key, str) or not key.strip() or any(ord(c) < 33 or ord(c) > 126 for c in key)):
        raise ValidationError("Enter a valid API key")
    connection = http.client.HTTPSConnection(host, timeout=timeout)
    try:
        headers = {"Accept": "application/json", "User-Agent": "VeriCode/0.1"}
        if key:
            headers["Authorization"] = "Bearer " + key
        body = None
        if payload is not None:
            body = json.dumps(payload, allow_nan=False).encode("utf-8")
            headers["Content-Type"] = "application/json"
        connection.request("POST" if payload is not None else "GET", path, body, headers)
        response = connection.getresponse()
        if response.status != 200:
            raise TransportError(f"Provider request rejected (HTTP {response.status}); check key, permissions and model access")
        raw = response.read(limit + 1)
        if len(raw) > limit:
            raise TransportError("Provider response exceeded the byte limit")
        return raw
    except (OSError, http.client.HTTPException):
        raise TransportError("Provider connection failed; no automatic retry") from None
    finally:
        connection.close()


def request_json(host, path, **kwargs):
    try:
        return decode_json(request_bytes(host, path, **kwargs))
    except (ValueError, UnicodeError):
        raise TransportError("Provider returned invalid JSON") from None


@dataclass(frozen=True)
class Price:
    input_per_million: float
    output_per_million: float
    source: str
    fetched_at: float
    input_ceiling: int | None = None

    def __post_init__(self):
        for value in (self.input_per_million, self.output_per_million):
            if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
                raise ValidationError("Provider prices must be finite non-negative numbers")
        if type(self.fetched_at) not in (int, float) or not math.isfinite(self.fetched_at):
            raise ValidationError("Invalid pricing timestamp")
        if self.input_ceiling is not None and (type(self.input_ceiling) is not int or not 1 <= self.input_ceiling <= 2_000_000):
            raise ValidationError("Invalid model context ceiling")

    def cost(self, input_tokens, output_tokens):
        return (Decimal(str(self.input_per_million)) * input_tokens +
                Decimal(str(self.output_per_million)) * output_tokens) / Decimal(1_000_000)


def parse_openai_prices(markdown, now=None):
    try:
        section = markdown.split("### Standard pricing data", 1)[1].split("###", 1)[0]
    except IndexError:
        raise TransportError("Official pricing table changed; no inferred prices used") from None
    result = {}
    for line in section.splitlines():
        if not line.startswith("|"):
            continue
        cells = [part.strip() for part in line.strip("|").split("|")]
        if len(cells) < 5 or not cells[1].startswith("$") or not cells[4].startswith("$"):
            continue
        name = cells[0].split(" (", 1)[0]
        try:
            result[name] = Price(float(cells[1].replace("$", "").replace(",", "")),
                                 float(cells[4].replace("$", "").replace(",", "")),
                                 PRICING_URL, now if now is not None else time.time())
        except ValueError:
            continue
    if not result:
        raise TransportError("Official standard pricing could not be read")
    return result


def verify_connection(provider, key):
    """Authenticate with a metadata GET and obtain priced text models, no inference."""
    if provider not in PROVIDERS:
        raise ValidationError("Select OpenAI or OpenRouter")
    host, prefix = PROVIDERS[provider]
    if provider == "openrouter":
        account = request_json(host, prefix + "/key", key=key)
        if not isinstance(account, dict) or not isinstance(account.get("data"), dict):
            raise TransportError("API key verification failed")
    models = request_json(host, prefix + "/models", key=key, limit=8 * 1024 * 1024)
    if not isinstance(models, dict) or not isinstance(models.get("data"), list):
        raise TransportError("Provider returned an invalid model catalog")
    if provider == "openai":
        raw = request_bytes("developers.openai.com", "/api/docs/pricing.md", limit=2 * 1024 * 1024)
        prices = parse_openai_prices(raw.decode("utf-8"))
        available = {row["id"] for row in models["data"] if isinstance(row, dict) and isinstance(row.get("id"), str)}
        excluded = ("audio", "realtime", "image", "transcribe", "tts", "search", "deep-research")
        return {name: price for name, price in prices.items() if name in available and not any(x in name for x in excluded)}
    result = {}
    for row in models["data"]:
        try:
            pricing = row["pricing"]
            if row["architecture"].get("output_modalities") != ["text"]:
                continue
            if "max_tokens" not in row.get("supported_parameters", []) or "response_format" not in row.get("supported_parameters", []):
                continue
            if any(Decimal(pricing.get(k, "0")) != 0 for k in ("request", "image", "web_search", "internal_reasoning")):
                continue
            result[row["id"]] = Price(float(Decimal(pricing["prompt"]) * 1_000_000),
                float(Decimal(pricing["completion"]) * 1_000_000), "https://openrouter.ai/api/v1/models", time.time(), row["context_length"])
        except (KeyError, TypeError, ValueError, ArithmeticError):
            continue
    return result


def nano(value):
    return int((Decimal(str(value)) * NANO).to_integral_value(rounding=ROUND_CEILING))


class SpendLedger:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS budgets (scope TEXT PRIMARY KEY, cap INTEGER NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS reservations (id TEXT PRIMARY KEY, scope TEXT NOT NULL, amount INTEGER NOT NULL, state TEXT NOT NULL)")

    def connect(self):
        return closing(sqlite3.connect(self.path, timeout=10, isolation_level=None))

    def authorize(self, scope, cap):
        if type(cap) not in (int, float) or not math.isfinite(cap) or not 0 < cap <= 10000:
            raise ValidationError("Set an explicit API spending limit between $0 and $10,000")
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            used = db.execute("SELECT COALESCE(SUM(amount),0) FROM reservations WHERE scope=?", (scope,)).fetchone()[0]
            if nano(cap) < used:
                db.rollback()
                raise ValidationError("New spending limit is below the amount already reserved/spent")
            db.execute("INSERT INTO budgets VALUES (?,?) ON CONFLICT(scope) DO UPDATE SET cap=excluded.cap", (scope, nano(cap)))
            db.commit()

    def reserve(self, scope, amount):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            budget = db.execute("SELECT cap FROM budgets WHERE scope=?", (scope,)).fetchone()
            rows = db.execute("SELECT amount,state FROM reservations WHERE scope=?", (scope,)).fetchall()
            if not budget or any(state != "settled" for _, state in rows):
                db.rollback()
                raise TransportError("Budget unavailable or an earlier call has an unresolved outcome; reconcile it before more calls")
            if sum(a for a, _ in rows) + nano(amount) > budget[0]:
                db.rollback()
                raise TransportError("API spending limit reached before sending a request")
            identity = str(uuid4())
            db.execute("INSERT INTO reservations VALUES (?,?,?,?)", (identity, scope, nano(amount), "pending"))
            db.commit()
            return identity

    def settle(self, identity, amount=None):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT amount,state FROM reservations WHERE id=?", (identity,)).fetchone()
            if not row or row[1] != "pending":
                db.rollback()
                raise TransportError("Invalid budget reservation")
            state = "uncertain" if amount is None or nano(amount) > row[0] else "settled"
            db.execute("UPDATE reservations SET amount=?,state=? WHERE id=?", (max(row[0], nano(amount)) if state == "uncertain" and amount is not None else row[0] if amount is None else nano(amount), state, identity))
            db.commit()
            return state

    def status(self, scope):
        with self.connect() as db:
            cap = db.execute("SELECT cap FROM budgets WHERE scope=?", (scope,)).fetchone()
            rows = db.execute("SELECT amount,state FROM reservations WHERE scope=?", (scope,)).fetchall()
        return {"cap_usd": cap[0] / NANO if cap else 0, "accounted_usd": sum(a for a, _ in rows) / NANO,
                "blocked": any(state != "settled" for _, state in rows), "calls": len(rows)}


@dataclass
class HostedConnection:
    provider: str
    model: str
    price: Price
    api_key: str = field(repr=False)
    cap_usd: float
    ledger: SpendLedger = field(repr=False)

    def __post_init__(self):
        if self.provider not in PROVIDERS or not self.api_key.strip():
            raise ValidationError("A verified provider connection is required")
        self.scope = hashlib.sha256((self.provider + "\0" + self.api_key).encode()).hexdigest()
        self.ledger.authorize(self.scope, self.cap_usd)

    def public_info(self):
        return {"provider": self.provider, "model": self.model, "pricing_source": self.price.source,
                "pricing_fetched_at": self.price.fetched_at, "input_usd_per_million": self.price.input_per_million,
                "output_usd_per_million": self.price.output_per_million,
                "cost_basis": "provider-reported USD cost" if self.provider == "openrouter" else "standard token-rate estimate; provider invoice is authoritative",
                "budget": self.ledger.status(self.scope), "cost_reporting": "provider-reported" if self.provider == "openrouter" else "estimated"}


@contextmanager
def use_connection(connection):
    token = _CONNECTION.set(connection)
    try:
        yield
    finally:
        _CONNECTION.reset(token)


class HostedTransport:
    offline = False

    def __init__(self, connection):
        self.connection = connection

    def complete(self, prompt, *, model, max_output_tokens, timeout_seconds):
        connection = self.connection
        if model != connection.model or not 0 <= time.time() - connection.price.fetched_at < 86400:
            raise TransportError("Connection/model changed or pricing expired; verify again")
        # Byte-level text tokenizers need no more tokens than UTF-8 bytes. Reserve
        # an additional 1024 framing tokens; no tools/images/audio are requested.
        bound = len(prompt.encode("utf-8")) + 1024
        if bound > 16384:
            raise TransportError("Hosted prompt exceeds the supported text context allowance")
        # OpenRouter may route across tokenizers. Reserve its entire advertised
        # context rather than assuming a tokenizer for an arbitrary model.
        if connection.provider == "openrouter":
            if connection.price.input_ceiling is None:
                raise TransportError("Model context ceiling unavailable; verify the catalog again")
            bound = connection.price.input_ceiling
        reservation = connection.ledger.reserve(connection.scope, connection.price.cost(bound, max_output_tokens))
        usage = Usage()
        try:
            host, prefix = PROVIDERS[connection.provider]
            payload = {"model": model, "messages": [{"role": "user", "content": prompt}],
                       "stream": False, "response_format": {"type": "json_object"}}
            payload["max_completion_tokens" if connection.provider == "openai" else "max_tokens"] = max_output_tokens
            if connection.provider == "openai":
                payload.update(store=False, service_tier="default")
            else:
                payload["provider"] = {"allow_fallbacks": False, "require_parameters": True,
                    "max_price": {"prompt": connection.price.input_per_million, "completion": connection.price.output_per_million}}
            result = request_json(host, prefix + "/chat/completions", key=connection.api_key,
                                  payload=payload, timeout=timeout_seconds)
            reported = result["usage"]
            input_tokens, output_tokens = reported["prompt_tokens"], reported["completion_tokens"]
            # OpenRouter reports USD cost directly. OpenAI reports tokens; use
            # its fetched standard rates and label that amount as an estimate.
            cost = reported.get("cost") if connection.provider == "openrouter" else float(connection.price.cost(input_tokens, output_tokens))
            usage = Usage(input_tokens, output_tokens, cost)
            if cost is None:
                raise TransportError("Provider cost is unknown", usage=usage)
            if input_tokens > bound or output_tokens > max_output_tokens:
                raise TransportError("Provider exceeded requested bounds", usage=usage)
            if connection.ledger.settle(reservation, usage.cost_usd) != "settled":
                raise TransportError("Provider cost exceeded its reservation", usage=usage)
            reservation = None
            choice = result["choices"][0]
            if choice.get("finish_reason") != "stop":
                raise TransportError("Provider response incomplete", usage=usage)
            return RawCompletion(choice["message"]["content"], usage, result.get("model"))
        except Exception:
            if reservation is not None:
                # A reservation already marked uncertain remains blocked.
                try:
                    connection.ledger.settle(reservation, None)
                except TransportError:
                    pass
            raise TransportError("Hosted request failed; check connection and budget status", usage=usage) from None


class BudgetedProvider(StructuredProvider):
    """Explicit trusted network-provider type accepted by repair controllers."""

    def __init__(self, connection, limits):
        self.connection = connection
        super().__init__(HostedTransport(connection), provider=connection.provider, model=connection.model, limits=limits)


def make_hosted_provider(config):
    connection = _CONNECTION.get()
    if connection is None or (connection.provider, connection.model) != (config.provider, config.model):
        raise ValidationError("Connect and authorize your own API key in Models & API before hosted repair")
    return BudgetedProvider(connection, config.generation)


def connection_metadata():
    connection = _CONNECTION.get()
    return {"hosted_connection": connection.public_info()} if connection else {}
