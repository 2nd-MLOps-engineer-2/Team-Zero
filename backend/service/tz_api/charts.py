"""Presentation normalization only; C's analytical calculations remain unchanged."""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext

SCALE = Decimal('0.00000001')


def positive(value):
    if value is None or value == '':
        return None
    try:
        number = Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        return None
    return number if number.is_finite() and number > 0 else None


def normalize_prices(rows):
    """Select one common positive-price base before pagination, never fill gaps."""
    ordered = sorted(rows, key=lambda row: row['trd_dt'])
    base = next((row for row in ordered if positive(row.get('close_prc')) is not None
                 and positive(row.get('idx_close_prc')) is not None), None)
    base_date = base['trd_dt'] if base else None

    def index(value, column):
        number = positive(value)
        if base is None or number is None:
            return None
        with localcontext() as context:
            context.prec = 64
            return format((number / positive(base[column]) * 100).quantize(SCALE, rounding=ROUND_HALF_UP), 'f')

    output = []
    for row in ordered:
        before = base is not None and row['trd_dt'] < base_date
        stock = None if before else index(row.get('close_prc'), 'close_prc')
        market = None if before else index(row.get('idx_close_prc'), 'idx_close_prc')
        status = ('NO_COMMON_BASE' if base is None else 'BEFORE_BASE_DATE' if before else
                  'OK' if stock is not None and market is not None else 'PARTIAL')
        output.append(dict(row, stock_base100=stock, market_base100=market,
                           price_base_date=base_date, price_chart_stts_cd=status))
    metadata = dict(price_base_date=base_date,
                    price_normalization=dict(rule='first_common_positive_observation_in_requested_window',
                                             base_value='100', scale=8, rounding='HALF_UP',
                                             stock_base_price=base['close_prc'] if base else None,
                                             market_base_price=base['idx_close_prc'] if base else None))
    return output, metadata
