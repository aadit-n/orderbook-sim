import ctypes
from ctypes import c_int, c_float, c_char_p, POINTER, Structure
from pathlib import Path
import streamlit as st
import pandas as pd
import time
import platform
import subprocess
from threading import Thread
import threading
from io import StringIO

st.set_page_config(
    page_title="Orderbook Simulator",
    page_icon="📈",
    layout="wide",
)

st.markdown(
    """
    <style>
      :root {
        --bg: #0f1419;
        --panel: #151b22;
        --panel-2: #1b2330;
        --accent: #f4c95d;
        --accent-2: #6ee7b7;
        --text: #e6edf3;
        --muted: #9aa4b2;
        --danger: #ff6b6b;
      }

      .stApp {
        background:
          radial-gradient(1200px 600px at 15% 0%, #1e2533 0%, transparent 60%),
          radial-gradient(900px 500px at 85% 10%, #1a2230 0%, transparent 60%),
          var(--bg);
        color: var(--text);
      }

      .block-container { padding-top: 2rem; }

      .title-wrap {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: linear-gradient(135deg, #1a2230 0%, #131a23 100%);
        border: 1px solid #202938;
        border-radius: 16px;
        padding: 16px 20px;
        margin-bottom: 16px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.25);
      }
      .title-wrap h1 { margin: 0; font-size: 1.6rem; }
      .title-meta { color: var(--muted); font-size: 0.9rem; }

      .metric-card {
        background: var(--panel);
        border: 1px solid #202938;
        border-radius: 14px;
        padding: 10px 12px;
      }

      .section-card {
        background: var(--panel);
        border: 1px solid #202938;
        border-radius: 14px;
        padding: 12px 14px;
        margin-bottom: 16px;
        box-shadow: 0 6px 18px rgba(0,0,0,0.2);
      }

      .section-title {
        font-weight: 600;
        color: var(--text);
        margin-bottom: 6px;
      }

      .stDataFrame, .stTable {
        background: var(--panel-2);
        border-radius: 12px;
        border: 1px solid #202938;
      }

      .stSidebar {
        background: #0e131a;
        border-right: 1px solid #202938;
      }

      .stButton>button {
        background: var(--accent);
        color: #111;
        border: 0;
        border-radius: 10px;
        padding: 0.55rem 1rem;
        font-weight: 600;
      }
      .stButton>button:hover { filter: brightness(0.95); }

      .badge {
        background: #1f2937;
        border: 1px solid #2b3445;
        color: var(--muted);
        border-radius: 999px;
        padding: 2px 10px;
        font-size: 0.75rem;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

def _load_native_lib() -> ctypes.CDLL:
    root = Path(__file__).resolve().parents[1]
    build_dir = root / "build"
    system = platform.system()
    if system == "Windows":
        lib_path = build_dir / "orderbook.dll"
    elif system == "Darwin":
        lib_path = build_dir / "liborderbook.dylib"
    else:
        lib_path = build_dir / "orderbook.so"

    if not lib_path.exists():
        if system != "Windows":
            build_dir.mkdir(parents=True, exist_ok=True)
            cmd = [
                "g++",
                "-shared",
                "-fPIC",
                "-o",
                str(lib_path),
                str(root / "src" / "order.cpp"),
                str(root / "src" / "orderbook.cpp"),
                str(root / "src" / "wrapper.cpp"),
                "-I",
                str(root / "include"),
                "-std=c++17",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0 or not lib_path.exists():
                st.error(
                    "Native library build failed.\n"
                    f"Command: {' '.join(cmd)}\n"
                    f"stdout:\n{result.stdout}\n"
                    f"stderr:\n{result.stderr}"
                )
                st.stop()
        else:
            st.error(
                f"Native library not found: {lib_path}\n"
                "Make sure it is built on this system before running the app."
            )
            st.stop()

    return ctypes.CDLL(str(lib_path))


lib = _load_native_lib()

from streamlit_autorefresh import st_autorefresh

class order(Structure):
    _fields_ = [
        ("id", c_int),
        ("side", c_char_p),
        ("quantity", c_int),
        ("price", c_float),
        ("time", c_int),
        ("type", c_char_p),
        ("status", c_char_p),
    ]


class OrderBook(Structure):
    pass


lib.creatBook.restype = POINTER(OrderBook)
lib.generate_random_order.argtypes = [POINTER(c_int), c_float]
lib.generate_random_order.restype = POINTER(order)
lib.set_random_config.argtypes = [c_float, c_float, c_float, c_int, c_int, c_int]
lib.add_order.argtypes = [POINTER(OrderBook), POINTER(order)]
lib.get_orderbook_snapshot.argtypes = [POINTER(OrderBook)]
lib.get_orderbook_snapshot.restype = ctypes.c_char_p
lib.get_fulfilled_snapshot.argtypes = [POINTER(OrderBook)]
lib.get_fulfilled_snapshot.restype = ctypes.c_char_p
lib.get_trades_snapshot.argtypes = [POINTER(OrderBook)]
lib.get_trades_snapshot.restype = ctypes.c_char_p
lib.make_user_order.argtypes = [c_int, c_char_p, c_int, c_float, c_char_p]
lib.make_user_order.restype = POINTER(order)

st.markdown(
    """
    <div class="title-wrap">
      <div>
        <h1>Live Order Book Simulation</h1>
        <div class="title-meta">Real-time matching • Configurable flow • Portfolio P&L</div>
      </div>
      <div class="badge">v1.0</div>
    </div>
    """,
    unsafe_allow_html=True,
)

if "initialized" not in st.session_state:
    st.session_state.book = lib.creatBook()
    st.session_state.nextID = c_int(1)

    st.session_state.starting_cash = 10_000.0
    st.session_state.cash = st.session_state.starting_cash
    st.session_state.position_qty = 0
    st.session_state.avg_cost = 0.0
    st.session_state.realized_pnl = 0.0

    st.session_state.user_orders = set()
    st.session_state.user_order_meta = {}

    st.session_state.run_event = threading.Event()
    st.session_state.thread = None
    st.session_state.basePrice = 100.0
    st.session_state.base_price_ref = c_float(st.session_state.basePrice)

    st.session_state.processed_trades = set()

    st.session_state.best_bid = 0
    st.session_state.best_ask = 0
    st.session_state.midprice = 0
    st.session_state.obi = 0
    st.session_state.relative_spread = 0
    st.session_state.depth_bid = 0
    st.session_state.depth_ask = 0
    st.session_state.vwap_bid = 0
    st.session_state.vwap_ask = 0
    st.session_state.ofi = 0
    st.session_state.queue_pressure = 0
    st.session_state.microprice = 0

    st.session_state.batch_size = 10
    st.session_state.refresh_interval_ms = 1500
    st.session_state.metrics_every = 3
    st.session_state.refresh_count = 0
    st.session_state.table_style_limit = 200

    st.session_state.anchor_mid = True
    st.session_state.tick_size = 0.01
    st.session_state.price_sigma = 1.5
    st.session_state.market_prob = 0.1
    st.session_state.expiry_seconds = 0
    st.session_state.min_qty = 1
    st.session_state.max_qty = 200

    st.session_state.initialized = True


def run_simulation(run_event, book, nextID, base_price_ref, batch_size):
    while run_event.is_set():
        for _ in range(batch_size):
            o = lib.generate_random_order(ctypes.byref(nextID), c_float(base_price_ref.value))
            lib.add_order(ctypes.cast(book, POINTER(OrderBook)), o)
        time.sleep(0.5)



st.sidebar.header("Simulation Controls")

batch_size = st.sidebar.slider(
    "Orders per tick",
    min_value=1,
    max_value=50,
    value=int(st.session_state.batch_size),
    step=1,
)
st.session_state.batch_size = batch_size

refresh_interval_ms = st.sidebar.slider(
    "UI refresh (ms)",
    min_value=1000,
    max_value=2000,
    value=int(st.session_state.refresh_interval_ms),
    step=250,
)
st.session_state.refresh_interval_ms = refresh_interval_ms

metrics_every = st.sidebar.slider(
    "Metrics update cadence (ticks)",
    min_value=1,
    max_value=10,
    value=int(st.session_state.metrics_every),
    step=1,
)
st.session_state.metrics_every = metrics_every

table_style_limit = st.sidebar.slider(
    "Row limit for table styling",
    min_value=50,
    max_value=500,
    value=int(st.session_state.table_style_limit),
    step=50,
)
st.session_state.table_style_limit = table_style_limit

st_autorefresh(interval=st.session_state.refresh_interval_ms, key="refresh")

can_change_cash = (
    len(st.session_state.processed_trades) == 0
    and st.session_state.position_qty == 0
)

starting_cash = st.sidebar.number_input(
    "Starting Cash",
    min_value=0.0,
    value=float(st.session_state.starting_cash),
    step=100.0,
    disabled=not can_change_cash,
)
if can_change_cash and starting_cash != st.session_state.starting_cash:
    st.session_state.starting_cash = starting_cash
    st.session_state.cash = starting_cash
    st.session_state.position_qty = 0
    st.session_state.avg_cost = 0.0
    st.session_state.realized_pnl = 0.0
    st.session_state.processed_trades = set()

base_price = st.sidebar.number_input(
    "Base Price", min_value=1.0, value=st.session_state.basePrice
)
st.session_state.basePrice = base_price

anchor_mid = st.sidebar.checkbox(
    "Anchor random prices to mid",
    value=bool(st.session_state.anchor_mid),
)
st.session_state.anchor_mid = anchor_mid

tick_size = st.sidebar.number_input(
    "Tick Size",
    min_value=0.0001,
    value=float(st.session_state.tick_size),
    step=0.01,
    format="%.4f",
)
st.session_state.tick_size = tick_size

price_sigma = st.sidebar.number_input(
    "Price Sigma",
    min_value=0.1,
    value=float(st.session_state.price_sigma),
    step=0.1,
)
st.session_state.price_sigma = price_sigma

market_prob = st.sidebar.slider(
    "Market Order %",
    min_value=0,
    max_value=50,
    value=int(st.session_state.market_prob * 100),
    step=1,
)
st.session_state.market_prob = market_prob / 100.0

expiry_seconds = st.sidebar.number_input(
    "Expiry Seconds (0 = GTC)",
    min_value=0,
    value=int(st.session_state.expiry_seconds),
    step=5,
)
st.session_state.expiry_seconds = expiry_seconds

min_qty = st.sidebar.number_input(
    "Min Qty",
    min_value=1,
    value=int(st.session_state.min_qty),
    step=1,
)
max_qty = st.sidebar.number_input(
    "Max Qty",
    min_value=int(min_qty),
    value=int(st.session_state.max_qty),
    step=10,
)
st.session_state.min_qty = min_qty
st.session_state.max_qty = max_qty

lib.set_random_config(
    c_float(st.session_state.tick_size),
    c_float(st.session_state.price_sigma),
    c_float(st.session_state.market_prob),
    c_int(st.session_state.expiry_seconds),
    c_int(st.session_state.min_qty),
    c_int(st.session_state.max_qty),
)

c1, c2 = st.sidebar.columns(2)

if c1.button("▶ Start"):
    st.session_state.run_event.set()
    book = st.session_state.book
    nextID = st.session_state.nextID
    base_price_ref = st.session_state.base_price_ref
    batch_size = st.session_state.batch_size

    if not st.session_state.thread or not st.session_state.thread.is_alive():
        st.session_state.thread = Thread(
            target=run_simulation,
            args=(st.session_state.run_event, book, nextID, base_price_ref, batch_size),
            daemon=True,
        )
        st.session_state.thread.start()

if c2.button("⏸ Stop"):
    st.session_state.run_event.clear()

st.sidebar.subheader("Place Manual Order")

side = st.sidebar.selectbox("Side", ["buy", "sell"])
qty = st.sidebar.number_input("Quantity", 1, 100, step=1)
price = st.sidebar.number_input("Price", 1.0, 1000.0, step=1.0)
otype = st.sidebar.selectbox("Type", ["limit", "market"])

if st.sidebar.button("Submit Order"):
    side_lower = side.lower()
    qty_int = int(qty)
    price_f = float(price)

    if side_lower == "sell" and qty_int > st.session_state.position_qty:
        st.warning("You cannot sell more than your current holdings!")
        st.stop()

    if side_lower == "buy" and otype == "limit":
        cost_est = price_f * qty_int
        if cost_est > st.session_state.cash:
            st.warning(
                f"Not enough cash. Needed ≈ {cost_est:.2f}, "
                f"available {st.session_state.cash:.2f}"
            )
            st.stop()

    oid = st.session_state.nextID.value
    st.session_state.nextID.value += 1

    st.session_state.user_orders.add(oid)
    st.session_state.user_order_meta[oid] = {
        "side": side_lower,
        "price": price_f,
        "qty": qty_int,
        "type": otype,
    }

    uo_ptr = lib.make_user_order(
        oid, side_lower.encode(), qty_int, price_f, otype.encode()
    )
    lib.add_order(ctypes.cast(st.session_state.book, POINTER(OrderBook)), uo_ptr)


snapshot_ptr = lib.get_orderbook_snapshot(
    ctypes.cast(st.session_state.book, POINTER(OrderBook))
)
snapshot = snapshot_ptr.decode("utf-8")


def highlight_user_orders(row):
    try:
        oid = int(row["ID"])
    except Exception:
        return [""] * len(row)
    if oid in st.session_state.user_orders:
        return ["background-color: #ffef99"] * len(row)
    return [""] * len(row)


if snapshot.strip():
    df = pd.read_csv(StringIO(snapshot))
    df["ID"] = df["ID"].astype(int)

    buy_df = df[df["SIDE"].str.lower() == "buy"].sort_values(
        "PRICE", ascending=False
    )
    sell_df = df[df["SIDE"].str.lower() == "sell"].sort_values(
        "PRICE", ascending=True
    )

    st.markdown('<div class="section-card"><div class="section-title">Order Book</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Buy Orders")
        if len(buy_df) <= st.session_state.table_style_limit:
            st.dataframe(buy_df.style.apply(highlight_user_orders, axis=1), use_container_width=True)
        else:
            st.dataframe(buy_df, use_container_width=True)
    with col2:
        st.subheader("Sell Orders")
        if len(sell_df) <= st.session_state.table_style_limit:
            st.dataframe(sell_df.style.apply(highlight_user_orders, axis=1), use_container_width=True)
        else:
            st.dataframe(sell_df, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
    has_bid = not buy_df.empty
    has_ask = not sell_df.empty

    local_best_bid = buy_df.iloc[0]["PRICE"] if has_bid else 0
    local_best_ask = sell_df.iloc[0]["PRICE"] if has_ask else 0

    st.session_state.best_bid = local_best_bid if has_bid else 0
    st.session_state.best_ask = local_best_ask if has_ask else 0

    if st.session_state.anchor_mid and has_bid and has_ask:
        st.session_state.base_price_ref.value = float(
            (local_best_bid + local_best_ask) / 2
        )
    else:
        st.session_state.base_price_ref.value = float(st.session_state.basePrice)

    st.session_state.refresh_count += 1
    if st.session_state.refresh_count % st.session_state.metrics_every == 0:
        if has_bid:
            st.session_state.depth_bid = buy_df["QTY"].sum()
            st.session_state.queue_pressure = buy_df.iloc[0]["QTY"] / st.session_state.depth_bid
            st.session_state.vwap_bid = (buy_df["PRICE"] * buy_df["QTY"]).sum() / st.session_state.depth_bid
        else:
            st.session_state.depth_bid = 0
            st.session_state.queue_pressure = 0
            st.session_state.vwap_bid = 0

        if has_ask:
            st.session_state.depth_ask = sell_df["QTY"].sum()
            st.session_state.vwap_ask = (sell_df["PRICE"] * sell_df["QTY"]).sum() / st.session_state.depth_ask
        else:
            st.session_state.depth_ask = 0
            st.session_state.vwap_ask = 0

        if has_bid and has_ask:
            bid = local_best_bid
            ask = local_best_ask

            st.session_state.midprice = (bid + ask) / 2
            st.session_state.obi = (bid - ask) / (bid + ask)
            st.session_state.relative_spread = (ask - bid) / st.session_state.midprice
            st.session_state.ofi = bid * buy_df.iloc[0]["QTY"] - ask * sell_df.iloc[0]["QTY"]
            st.session_state.microprice = (
                ask * buy_df.iloc[0]["QTY"] + bid * sell_df.iloc[0]["QTY"]
            ) / (buy_df.iloc[0]["QTY"] + sell_df.iloc[0]["QTY"])
        else:
            st.session_state.midprice = 0
            st.session_state.obi = 0
            st.session_state.relative_spread = 0
            st.session_state.ofi = 0
            st.session_state.microprice = 0
else:
    st.info("Order book is empty.")

st.markdown('<div class="section-card"><div class="section-title">Market Snapshot</div>', unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Best Bid", f"${st.session_state.best_bid:.2f}")
    st.metric("Best Ask", f"${st.session_state.best_ask:.2f}")
    st.metric("Midprice", f"${st.session_state.midprice:.2f}")
with c2:
    st.metric("OBI", f"{st.session_state.obi:.2f}")
    st.metric("Relative Spread", f"{st.session_state.relative_spread:.2f}")
    st.metric("Depth Bid", f"{st.session_state.depth_bid}")
with c3:
    st.metric("Depth Ask", f"{st.session_state.depth_ask}")
    st.metric("VWAP Bid", f"${st.session_state.vwap_bid:.2f}")
    st.metric("VWAP Ask", f"${st.session_state.vwap_ask:.2f}")
with c4:
    st.metric("OFI", f"{st.session_state.ofi:.2f}")
    st.metric("Queue Pressure", f"{st.session_state.queue_pressure:.2f}")
    st.metric("Microprice", f"${st.session_state.microprice:.2f}")
st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="section-card"><div class="section-title">Trades</div>', unsafe_allow_html=True)

trades_ptr = lib.get_trades_snapshot(
    ctypes.cast(st.session_state.book, POINTER(OrderBook))
)
trades = trades_ptr.decode("utf-8")

df_trades = None
if trades.strip():
    df_trades = pd.read_csv(StringIO(trades))

    if "TRADE_ID" in df_trades.columns:
        df_trades["TRADE_ID"] = df_trades["TRADE_ID"].astype(int)
    if "ORDER_ID" in df_trades.columns:
        df_trades["ORDER_ID"] = df_trades["ORDER_ID"].astype(int)
    if "QUANTITY" in df_trades.columns:
        df_trades["QUANTITY"] = df_trades["QUANTITY"].astype(int)
    if "PRICE" in df_trades.columns:
        df_trades["PRICE"] = df_trades["PRICE"].astype(float)

    st.dataframe(df_trades)
else:
    st.info("No trades executed yet.")

st.markdown("</div>", unsafe_allow_html=True)
st.markdown('<div class="section-card"><div class="section-title">Order Events (Cancelled/Expired)</div>', unsafe_allow_html=True)

fulfilled_ptr = lib.get_fulfilled_snapshot(
    ctypes.cast(st.session_state.book, POINTER(OrderBook))
)
fulfilled = fulfilled_ptr.decode("utf-8")

df_fulfilled = None
if fulfilled.strip():
    df_fulfilled = pd.read_csv(StringIO(fulfilled))

    if "ID" in df_fulfilled.columns:
        df_fulfilled["ID"] = df_fulfilled["ID"].astype(int)
    if "QUANTITY" in df_fulfilled.columns:
        df_fulfilled["QUANTITY"] = df_fulfilled["QUANTITY"].astype(int)
    if "PRICE" in df_fulfilled.columns:
        df_fulfilled["PRICE"] = df_fulfilled["PRICE"].astype(float)

    st.dataframe(df_fulfilled)
else:
    st.info("No order events yet.")
st.markdown("</div>", unsafe_allow_html=True)


def update_user_pnl(trade_row: pd.Series):
    tid = int(trade_row["TRADE_ID"])
    if tid in st.session_state.processed_trades:
        return

    st.session_state.processed_trades.add(tid)

    side = str(trade_row["SIDE"]).lower()
    price = float(trade_row["PRICE"])
    qty = int(trade_row["QUANTITY"])

    if qty <= 0:
        return

    if side == "buy":
        cost = price * qty
        st.session_state.cash -= cost

        prev_qty = st.session_state.position_qty
        new_qty = prev_qty + qty

        if new_qty > 0:
            total_before = st.session_state.avg_cost * prev_qty
            total_after = total_before + cost
            st.session_state.avg_cost = total_after / new_qty

        st.session_state.position_qty = new_qty

    else:
        realized = (price - st.session_state.avg_cost) * qty
        st.session_state.realized_pnl += realized

        st.session_state.cash += price * qty
        st.session_state.position_qty -= qty

        if st.session_state.position_qty == 0:
            st.session_state.avg_cost = 0.0


st.markdown('<div class="section-card"><div class="section-title">User Orders & P&L</div>', unsafe_allow_html=True)

user_trades = None
if df_trades is not None and not df_trades.empty:
    user_trades = df_trades[df_trades["ORDER_ID"].isin(st.session_state.user_orders)]
    user_trades = user_trades[user_trades["QUANTITY"] > 0]
    user_trades = user_trades.sort_values("TRADE_ID")

    for _, t in user_trades.iterrows():
        update_user_pnl(t)

    last_prices = df_trades["PRICE"].tail(5)
    last_price = float(last_prices.mean()) if len(last_prices) > 0 else st.session_state.avg_cost

    unrealized = (last_price - st.session_state.avg_cost) * st.session_state.position_qty
    total_pnl = st.session_state.realized_pnl + unrealized

    cA, cB, cC = st.columns(3)
    with cA:
        st.metric("Cash", f"${st.session_state.cash:,.2f}")
        st.metric("Position Qty", f"{st.session_state.position_qty}")
    with cB:
        st.metric("Average Cost", f"${st.session_state.avg_cost:.2f}")
        st.metric("Realized P&L", f"${st.session_state.realized_pnl:.2f}")
    with cC:
        st.metric("Unrealized P&L", f"${unrealized:.2f}")
        st.metric("Total P&L", f"${total_pnl:.2f}")
else:
    st.info("No trades executed yet.")

rows = []
order_pnl = {}
if user_trades is not None and not user_trades.empty:
    pos_qty = 0
    avg_cost = 0.0
    for _, t in user_trades.iterrows():
        oid = int(t["ORDER_ID"])
        side = str(t["SIDE"]).lower()
        price = float(t["PRICE"])
        qty = int(t["QUANTITY"])
        if side == "buy":
            total_before = avg_cost * pos_qty
            pos_qty += qty
            avg_cost = (total_before + price * qty) / pos_qty if pos_qty > 0 else 0.0
        else:
            realized = (price - avg_cost) * qty
            order_pnl[oid] = order_pnl.get(oid, 0.0) + realized
            pos_qty -= qty
            if pos_qty == 0:
                avg_cost = 0.0

filled_qty = {}
avg_fill_price = {}
if user_trades is not None and not user_trades.empty:
    grouped = user_trades.groupby("ORDER_ID")
    filled_qty = grouped["QUANTITY"].sum().to_dict()
    avg_fill_price = (grouped.apply(lambda g: (g["PRICE"] * g["QUANTITY"]).sum() / g["QUANTITY"].sum())
                      ).to_dict()

for oid in sorted(st.session_state.user_orders):
    meta = st.session_state.user_order_meta.get(oid, {})
    side = meta.get("side", "")
    qty = int(meta.get("qty", 0))
    price = float(meta.get("price", 0.0))
    otype = meta.get("type", "")
    fqty = int(filled_qty.get(oid, 0))
    avg_px = float(avg_fill_price.get(oid, 0.0)) if fqty > 0 else 0.0
    remaining = max(qty - fqty, 0)
    if fqty == 0:
        status = "open"
    elif fqty < qty:
        status = "partially_filled"
    else:
        status = "filled"

    rows.append(
        {
            "ORDER_ID": oid,
            "SIDE": side,
            "TYPE": otype,
            "ORDER_QTY": qty,
            "ORDER_PRICE": price,
            "FILLED_QTY": fqty,
            "AVG_FILL_PRICE": avg_px,
            "REMAINING": remaining,
            "STATUS": status,
            "REALIZED_PNL": order_pnl.get(oid, 0.0) if side == "sell" else 0.0,
        }
    )

if rows:
    df_orders = pd.DataFrame(rows)
    st.dataframe(df_orders, use_container_width=True)
else:
    st.info("No user orders yet.")
st.markdown("</div>", unsafe_allow_html=True)
