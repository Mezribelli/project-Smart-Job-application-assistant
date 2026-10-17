"""Sample Python solution used to demonstrate the code-analysis agent."""


def net_asset_value(total_assets: float, total_liabilities: float, shares: int) -> float:
    """Return the NAV per share.

    >>> net_asset_value(1000.0, 400.0, 100)
    6.0
    >>> net_asset_value(10.0, 10.0, 3)
    0.0
    """
    if shares == 0:
        return 0.0
    return (total_assets - total_liabilities) / shares


class PositionValuation:
    """Value a single fund position."""

    def __init__(self, quantity: float, price: float) -> None:
        self.quantity = quantity
        self.price = price

    def market_value(self) -> float:
        return round(self.quantity * self.price, 2)

    def unrealised_pnl(self, cost_basis: float) -> float:
        if self.quantity <= 0:
            return 0.0
        return self.market_value() - cost_basis * self.quantity
