import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from io import BytesIO
import base64


INTERVAL_MAX_PERIOD = {
    '1m':  '7d',
    '2m':  '60d',
    '5m':  '60d',
    '15m': '60d',
    '30m': '60d',
    '60m': '730d',
    '1h':  '730d',
    '90m': '60d',
    '1d':  '10y',
    '5d':  '10y',
    '1wk': '10y',
    '1mo': 'max',
}


def fetch_data(ticker: str, period: str, interval: str) -> pd.DataFrame:
    df = yf.download(
        ticker, period=period, interval=interval,
        progress=False, auto_adjust=True
    )

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    if df.empty:
        raise ValueError(f"No data found for '{ticker}'. Check the ticker symbol.")

    df = df[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()
    return df


def fetch_exchange_rate(to_currency: str) -> float:
    if to_currency == 'USD':
        return 1.0
    rate_df = yf.download(
        f'USD{to_currency}=X', period='1d', interval='1m',
        progress=False, auto_adjust=True
    )
    if isinstance(rate_df.columns, pd.MultiIndex):
        rate_df.columns = rate_df.columns.get_level_values(0)
    if rate_df.empty:
        raise ValueError(f"Could not fetch exchange rate for USD → {to_currency}.")
    return float(rate_df['Close'].iloc[-1])


def find_swing_highs_lows(df: pd.DataFrame, window: int = 3):
    highs = df['High'].values
    lows = df['Low'].values
    n = len(df)

    swing_highs = []
    swing_lows = []

    for i in range(window, n - window):
        local_highs = highs[i - window: i + window + 1]
        local_lows = lows[i - window: i + window + 1]

        if highs[i] == local_highs.max():
            swing_highs.append(i)
        if lows[i] == local_lows.min():
            swing_lows.append(i)

    return swing_highs, swing_lows


def detect_bos_choch(df: pd.DataFrame, swing_highs: list, swing_lows: list):
    closes = df['Close'].values
    highs = df['High'].values
    lows = df['Low'].values
    n = len(df)

    signals = []
    trend = None

    sh_sorted = sorted(swing_highs)
    sl_sorted = sorted(swing_lows)
    broken_sh = set()
    broken_sl = set()

    def last_active_sh(before_idx):
        for idx in reversed(sh_sorted):
            if idx < before_idx and idx not in broken_sh:
                return idx, float(highs[idx])
        return None, None

    def last_active_sl(before_idx):
        for idx in reversed(sl_sorted):
            if idx < before_idx and idx not in broken_sl:
                return idx, float(lows[idx])
        return None, None

    for i in range(n):
        sh_idx, sh_price = last_active_sh(i)
        sl_idx, sl_price = last_active_sl(i)

        close = float(closes[i])

        if sh_idx is not None and close > sh_price:
            sig_type = 'CHoCH' if trend == 'down' else 'BOS'
            trend = 'up'
            signals.append({
                'index': i,
                'datetime': df.index[i],
                'type': sig_type,
                'direction': 'bullish',
                'price': close,
                'level': sh_price,
            })
            broken_sh.add(sh_idx)

        if sl_idx is not None and close < sl_price:
            sig_type = 'CHoCH' if trend == 'up' else 'BOS'
            trend = 'down'
            signals.append({
                'index': i,
                'datetime': df.index[i],
                'type': sig_type,
                'direction': 'bearish',
                'price': close,
                'level': sl_price,
            })
            broken_sl.add(sl_idx)

    return signals, trend


def _format_date(ts) -> str:
    try:
        return str(ts)[:16]
    except Exception:
        return str(ts)


def generate_chart(df: pd.DataFrame, swing_highs: list, swing_lows: list,
                   signals: list, ticker: str, currency_symbol: str = '$') -> str:
    n = len(df)
    xs = np.arange(n)

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(14, 8),
        gridspec_kw={'height_ratios': [3, 1]},
        facecolor='#0d1117'
    )

    for ax in (ax1, ax2):
        ax.set_facecolor('#0d1117')
        for spine in ax.spines.values():
            spine.set_edgecolor('#30363d')
        ax.tick_params(colors='#8b949e', labelsize=8)
        ax.grid(True, color='#21262d', linewidth=0.6, linestyle='--')

    # High-Low band
    ax1.fill_between(xs, df['Low'].values, df['High'].values,
                     alpha=0.08, color='#58a6ff')

    # Close line
    ax1.plot(xs, df['Close'].values, color='#58a6ff', linewidth=1.4,
             label='Close', zorder=3)

    # Swing highs
    if swing_highs:
        sh_y = [float(df['High'].iloc[i]) for i in swing_highs]
        ax1.scatter(swing_highs, sh_y, marker='^', color='#f85149',
                    s=70, zorder=5, label='Swing High')

    # Swing lows
    if swing_lows:
        sl_y = [float(df['Low'].iloc[i]) for i in swing_lows]
        ax1.scatter(swing_lows, sl_y, marker='v', color='#3fb950',
                    s=70, zorder=5, label='Swing Low')

    # BOS / CHoCH markers
    bos_bull_xs, bos_bull_ys = [], []
    bos_bear_xs, bos_bear_ys = [], []
    choch_xs, choch_ys = [], []
    label_done = {'BOS_bullish': False, 'BOS_bearish': False, 'CHoCH': False}

    for sig in signals:
        idx = sig['index']
        price = sig['price']
        is_bull = sig['direction'] == 'bullish'

        if sig['type'] == 'BOS':
            color = '#3fb950' if is_bull else '#f85149'
            ax1.axvline(idx, color=color, alpha=0.25, linewidth=0.8, zorder=2)
            key = 'BOS_bullish' if is_bull else 'BOS_bearish'
            lbl = ('BOS ▲' if is_bull else 'BOS ▼') if not label_done[key] else None
            label_done[key] = True
            ax1.annotate(
                'BOS', xy=(idx, price),
                xytext=(4, 6 if is_bull else -10),
                textcoords='offset points',
                color=color, fontsize=6.5, fontweight='bold',
                zorder=6
            )
        else:  # CHoCH
            ax1.axvline(idx, color='#bc8cff', alpha=0.35, linewidth=1.0, zorder=2)
            lbl = 'CHoCH' if not label_done['CHoCH'] else None
            label_done['CHoCH'] = True
            ax1.annotate(
                'CHoCH', xy=(idx, price),
                xytext=(4, 6 if is_bull else -12),
                textcoords='offset points',
                color='#bc8cff', fontsize=6.5, fontweight='bold',
                zorder=6
            )

    # Volume bars
    vol_colors = [
        '#3fb950' if float(df['Close'].iloc[i]) >= float(df['Open'].iloc[i])
        else '#f85149'
        for i in range(n)
    ]
    ax2.bar(xs, df['Volume'].values, color=vol_colors, alpha=0.75, width=0.8)
    ax2.set_ylabel('Volume', color='#8b949e', fontsize=8)

    # X-axis tick labels (dates)
    step = max(1, n // 10)
    tick_positions = list(range(0, n, step))
    tick_labels = [str(df.index[i])[:10] for i in tick_positions]
    for ax in (ax1, ax2):
        ax.set_xticks(tick_positions)
        ax.set_xticklabels(tick_labels, rotation=40, ha='right', fontsize=7)

    ax1.set_xlim(-1, n)
    ax2.set_xlim(-1, n)

    ax1.set_ylabel(f'Price ({currency_symbol})', color='#8b949e', fontsize=8)
    ax1.set_title(f'{ticker}  —  Technical Structure Analysis',
                  color='#c9d1d9', fontsize=12, fontweight='bold', pad=10)
    ax1.legend(facecolor='#161b22', edgecolor='#30363d',
               labelcolor='#c9d1d9', fontsize=8, loc='upper left')

    fig.tight_layout(pad=1.5)

    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=110, bbox_inches='tight',
                facecolor='#0d1117')
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()


def calculate_metrics(df: pd.DataFrame, signals: list,
                      swing_highs: list, swing_lows: list, trend) -> dict:
    current = float(df['Close'].iloc[-1])
    start = float(df['Close'].iloc[0])
    change = current - start
    change_pct = (change / start) * 100

    bos_count = sum(1 for s in signals if s['type'] == 'BOS')
    choch_count = sum(1 for s in signals if s['type'] == 'CHoCH')

    if trend == 'up':
        forecast = 'Bullish structure — market printing higher highs and higher lows.'
    elif trend == 'down':
        forecast = 'Bearish structure — market printing lower highs and lower lows.'
    else:
        forecast = 'No clear structure detected yet.'

    last_choch = next(
        (s for s in reversed(signals) if s['type'] == 'CHoCH'), None
    )

    return {
        'current_price': round(current, 4),
        'period_high': round(float(df['High'].max()), 4),
        'period_low': round(float(df['Low'].min()), 4),
        'price_change': round(change, 4),
        'price_change_pct': round(change_pct, 2),
        'avg_volume': int(df['Volume'].mean()),
        'trend': trend or 'undefined',
        'forecast': forecast,
        'bos_count': bos_count,
        'choch_count': choch_count,
        'swing_high_count': len(swing_highs),
        'swing_low_count': len(swing_lows),
        'total_signals': len(signals),
        'last_choch': {
            'datetime': _format_date(last_choch['datetime']),
            'direction': last_choch['direction'],
            'price': round(last_choch['price'], 4),
        } if last_choch else None,
    }


def run_analysis(ticker: str, period: str, interval: str,
                 swing_window: int = 3, currency: str = 'USD') -> dict:
    df = fetch_data(ticker, period, interval)

    currency = currency.upper()
    exchange_rate = fetch_exchange_rate(currency)
    if exchange_rate != 1.0:
        for col in ('Open', 'High', 'Low', 'Close'):
            df[col] = df[col] * exchange_rate

    currency_symbol = '€' if currency == 'EUR' else '$'

    swing_highs, swing_lows = find_swing_highs_lows(df, window=swing_window)
    signals, trend = detect_bos_choch(df, swing_highs, swing_lows)
    metrics = calculate_metrics(df, signals, swing_highs, swing_lows, trend)
    chart_b64 = generate_chart(df, swing_highs, swing_lows, signals,
                               ticker.upper(), currency_symbol=currency_symbol)

    swing_high_data = [
        {'datetime': _format_date(df.index[i]),
         'price': round(float(df['High'].iloc[i]), 4)}
        for i in swing_highs[-15:]
    ]
    swing_low_data = [
        {'datetime': _format_date(df.index[i]),
         'price': round(float(df['Low'].iloc[i]), 4)}
        for i in swing_lows[-15:]
    ]
    signal_data = [
        {
            'datetime': _format_date(s['datetime']),
            'type': s['type'],
            'direction': s['direction'],
            'price': round(s['price'], 4),
            'broken_level': round(s['level'], 4),
        }
        for s in signals
    ]

    return {
        'ticker': ticker.upper(),
        'period': period,
        'interval': interval,
        'currency': currency,
        'currency_symbol': currency_symbol,
        'exchange_rate': round(exchange_rate, 6),
        'data_points': len(df),
        'metrics': metrics,
        'chart': chart_b64,
        'swing_highs': swing_high_data,
        'swing_lows': swing_low_data,
        'signals': signal_data,
    }
