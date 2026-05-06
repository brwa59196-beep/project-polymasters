"""Detect no-arbitrage violations between European call options.

The scanner works with call quotes for one underlying and one expiry. It checks
classic call-call relationships across strikes:

* lower-strike calls cannot be cheaper than higher-strike calls;
* a vertical call spread cannot be worth more than the discounted strike gap;
* call prices must be convex in strike.

The implementation intentionally keeps the hot path simple: after sorting quotes,
vertical checks are linear and convexity is checked through adjacent strike slopes.
For a sorted discrete surface, adjacent slope monotonicity is enough to imply the
three-strike convexity inequality for every triplet, while avoiding an O(n^3)
scan of all butterflies.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Iterable, Sequence


@dataclass(frozen=True, slots=True)
class CallQuote:
    """A European call quote for a single expiry.

    Attributes:
        strike: Option strike price. Must be positive.
        price: Tradable call price. Must be non-negative.
        symbol: Optional quote identifier used in generated trade legs.
    """

    strike: float
    price: float
    symbol: str | None = None

    def __post_init__(self) -> None:
        if not isfinite(self.strike) or self.strike <= 0:
            raise ValueError("strike must be a positive finite number")
        if not isfinite(self.price) or self.price < 0:
            raise ValueError("price must be a non-negative finite number")


@dataclass(frozen=True, slots=True)
class Leg:
    """A leg in a static arbitrage portfolio."""

    action: str
    quantity: float
    instrument: str


@dataclass(frozen=True, slots=True)
class ArbitrageOpportunity:
    """Description of a call-call arbitrage opportunity.

    The listed legs are opened at time zero. Positive ``net_credit`` means the
    portfolio receives money up front before any hedge-financing leg is funded.
    """

    kind: str
    description: str
    net_credit: float
    legs: tuple[Leg, ...]
    strikes: tuple[float, ...]


def find_call_call_arbitrage(
    quotes: Iterable[CallQuote],
    *,
    discount_factor: float = 1.0,
    tolerance: float = 1e-9,
) -> list[ArbitrageOpportunity]:
    """Find static arbitrage opportunities among same-expiry call quotes.

    Args:
        quotes: Call quotes for the same underlying and expiration.
        discount_factor: Present value of one currency unit paid at expiration.
            For a continuously-compounded risk-free rate ``r`` and time ``t``,
            this is ``exp(-r * t)``. It must be positive and no greater than 1.
        tolerance: Numerical threshold used to ignore tiny floating-point noise.

    Returns:
        A list of detected opportunities. The function checks adjacent vertical
        spreads and adjacent-slope convexity after sorting quotes by strike, so
        the scan is O(n log n) including sorting and O(n) on already sorted data.
    """

    if not isfinite(discount_factor) or not 0 < discount_factor <= 1:
        raise ValueError("discount_factor must be in the interval (0, 1]")
    if not isfinite(tolerance) or tolerance < 0:
        raise ValueError("tolerance must be a non-negative finite number")

    ordered = _deduplicate_and_sort(quotes)
    opportunities: list[ArbitrageOpportunity] = []
    opportunities.extend(_find_vertical_violations(ordered, discount_factor, tolerance))
    opportunities.extend(_find_convexity_violations(ordered, tolerance))
    return opportunities


def _deduplicate_and_sort(quotes: Iterable[CallQuote]) -> tuple[CallQuote, ...]:
    ordered = sorted(quotes, key=lambda quote: quote.strike)
    seen: set[float] = set()
    for quote in ordered:
        if quote.strike in seen:
            raise ValueError(f"duplicate strike: {quote.strike:g}")
        seen.add(quote.strike)
    return tuple(ordered)


def _find_vertical_violations(
    quotes: Sequence[CallQuote], discount_factor: float, tolerance: float
) -> list[ArbitrageOpportunity]:
    opportunities: list[ArbitrageOpportunity] = []
    for lower, higher in zip(quotes, quotes[1:]):
        spread_price = lower.price - higher.price
        max_spread_price = discount_factor * (higher.strike - lower.strike)

        if spread_price < -tolerance:
            opportunities.append(
                ArbitrageOpportunity(
                    kind="monotonicity",
                    description=(
                        "Lower-strike call is cheaper than higher-strike call; "
                        "buy the lower strike and sell the higher strike."
                    ),
                    net_credit=-spread_price,
                    legs=(
                        _option_leg("buy", 1.0, lower),
                        _option_leg("sell", 1.0, higher),
                    ),
                    strikes=(lower.strike, higher.strike),
                )
            )

        if spread_price > max_spread_price + tolerance:
            opportunities.append(
                ArbitrageOpportunity(
                    kind="vertical_spread_upper_bound",
                    description=(
                        "Call spread is overpriced relative to the discounted "
                        "strike gap; sell the spread and lend the gap's present value."
                    ),
                    net_credit=spread_price - max_spread_price,
                    legs=(
                        _option_leg("sell", 1.0, lower),
                        _option_leg("buy", 1.0, higher),
                        Leg("lend", max_spread_price, "cash_until_expiry"),
                    ),
                    strikes=(lower.strike, higher.strike),
                )
            )

    return opportunities


def _find_convexity_violations(
    quotes: Sequence[CallQuote], tolerance: float
) -> list[ArbitrageOpportunity]:
    opportunities: list[ArbitrageOpportunity] = []
    for left, middle, right in zip(quotes, quotes[1:], quotes[2:]):
        left_slope = (middle.price - left.price) / (middle.strike - left.strike)
        right_slope = (right.price - middle.price) / (right.strike - middle.strike)

        if left_slope > right_slope + tolerance:
            left_weight, right_weight = _wing_weights(
                left.strike, middle.strike, right.strike
            )
            synthetic_middle_price = left_weight * left.price + right_weight * right.price
            violation = middle.price - synthetic_middle_price
            opportunities.append(
                ArbitrageOpportunity(
                    kind="convexity",
                    description=(
                        "Middle-strike call is overpriced versus a "
                        "strike-weighted portfolio of adjacent wing calls; sell "
                        "the middle strike and buy the wings."
                    ),
                    net_credit=violation,
                    legs=(
                        _option_leg("buy", left_weight, left),
                        _option_leg("sell", 1.0, middle),
                        _option_leg("buy", right_weight, right),
                    ),
                    strikes=(left.strike, middle.strike, right.strike),
                )
            )

    return opportunities


def _wing_weights(
    left_strike: float, middle_strike: float, right_strike: float
) -> tuple[float, float]:
    width = right_strike - left_strike
    return (
        (right_strike - middle_strike) / width,
        (middle_strike - left_strike) / width,
    )


def _option_leg(action: str, quantity: float, quote: CallQuote) -> Leg:
    label = quote.symbol or f"call_{quote.strike:g}"
    return Leg(action=action, quantity=quantity, instrument=label)
