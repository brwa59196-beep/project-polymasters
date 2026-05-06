import pytest

from polymasters.call_call_arbitrage import CallQuote, find_call_call_arbitrage


def test_monotonicity_violation_creates_buy_low_sell_high_trade():
    opportunities = find_call_call_arbitrage(
        [CallQuote(100, 4.0, "C100"), CallQuote(110, 5.5, "C110")]
    )

    assert len(opportunities) == 1
    opportunity = opportunities[0]
    assert opportunity.kind == "monotonicity"
    assert opportunity.net_credit == pytest.approx(1.5)
    assert [(leg.action, leg.quantity, leg.instrument) for leg in opportunity.legs] == [
        ("buy", 1.0, "C100"),
        ("sell", 1.0, "C110"),
    ]


def test_vertical_spread_upper_bound_violation_includes_cash_lending_leg():
    opportunities = find_call_call_arbitrage(
        [CallQuote(100, 15.0), CallQuote(110, 2.0)], discount_factor=0.95
    )

    assert len(opportunities) == 1
    opportunity = opportunities[0]
    assert opportunity.kind == "vertical_spread_upper_bound"
    assert opportunity.net_credit == pytest.approx(3.5)
    assert opportunity.legs[-1].action == "lend"
    assert opportunity.legs[-1].quantity == pytest.approx(9.5)


def test_convexity_violation_creates_weighted_butterfly_trade():
    opportunities = find_call_call_arbitrage(
        [CallQuote(90, 12.0), CallQuote(100, 11.0), CallQuote(120, 2.0)]
    )

    convexity_opportunities = [item for item in opportunities if item.kind == "convexity"]
    assert len(convexity_opportunities) == 1
    opportunity = convexity_opportunities[0]
    assert opportunity.net_credit == pytest.approx(7 / 3)
    assert [(leg.action, leg.quantity) for leg in opportunity.legs] == [
        ("buy", pytest.approx(2 / 3)),
        ("sell", 1.0),
        ("buy", pytest.approx(1 / 3)),
    ]


def test_valid_surface_has_no_opportunities():
    opportunities = find_call_call_arbitrage(
        [CallQuote(90, 18.0), CallQuote(100, 10.0), CallQuote(110, 4.0)]
    )

    assert opportunities == []


def test_rejects_duplicate_strikes():
    with pytest.raises(ValueError, match="duplicate strike"):
        find_call_call_arbitrage([CallQuote(100, 1.0), CallQuote(100, 1.1)])
