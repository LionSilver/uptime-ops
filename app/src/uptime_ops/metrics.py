from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

CHECKS_TOTAL = Counter(
    "uptime_checks_total",
    "Total number of URL checks",
    ["target", "result"],
)
DOWN_GAUGE = Gauge(
    "uptime_target_down",
    "1 if the target is currently down, else 0",
    ["target"],
)
LATENCY = Histogram(
    "uptime_latency_ms",
    "Check latency in milliseconds",
    ["target"],
    buckets=(50, 100, 250, 500, 1000, 2500, 5000, 10000),
)


def observe(url: str, up: bool, latency_ms: float) -> None:
    CHECKS_TOTAL.labels(target=url, result="up" if up else "down").inc()
    DOWN_GAUGE.labels(target=url).set(0 if up else 1)
    LATENCY.labels(target=url).observe(latency_ms)


def render() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST
