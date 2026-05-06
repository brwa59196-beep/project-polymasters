"""Micro-benchmark for the call-call arbitrage scanner.

Run from the repository root:

    python scripts/benchmark_call_call.py --quotes 500 --iterations 1000

This benchmark measures in-process scan time only. It does not include market
feed handling, broker/exchange gateways, network hops, order acknowledgements,
or production risk checks.
"""

from __future__ import annotations

import argparse
import statistics
from pathlib import Path
import sys
from time import perf_counter_ns

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from polymasters.call_call_arbitrage import CallQuote, find_call_call_arbitrage


def build_quotes(count: int) -> list[CallQuote]:
    """Build a smooth synthetic call curve with no intentional violations."""

    return [
        CallQuote(strike=50.0 + index, price=max(150.0 - index, 0.01))
        for index in range(count)
    ]


def run_benchmark(quotes: list[CallQuote], iterations: int) -> list[int]:
    durations_ns: list[int] = []
    for _ in range(iterations):
        started_at = perf_counter_ns()
        find_call_call_arbitrage(quotes, discount_factor=1.0)
        durations_ns.append(perf_counter_ns() - started_at)
    return durations_ns


def percentile(sorted_values: list[int], percent: float) -> int:
    index = round((len(sorted_values) - 1) * percent)
    return sorted_values[index]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quotes", type=int, default=500, help="number of call quotes")
    parser.add_argument("--iterations", type=int, default=1000, help="benchmark loops")
    args = parser.parse_args()

    if args.quotes < 3:
        raise SystemExit("--quotes must be at least 3")
    if args.iterations < 1:
        raise SystemExit("--iterations must be at least 1")

    durations = sorted(run_benchmark(build_quotes(args.quotes), args.iterations))
    mean_ms = statistics.fmean(durations) / 1_000_000
    print(f"quotes={args.quotes} iterations={args.iterations}")
    print(f"mean_ms={mean_ms:.4f}")
    print(f"p50_ms={percentile(durations, 0.50) / 1_000_000:.4f}")
    print(f"p95_ms={percentile(durations, 0.95) / 1_000_000:.4f}")
    print(f"p99_ms={percentile(durations, 0.99) / 1_000_000:.4f}")


if __name__ == "__main__":
    main()
