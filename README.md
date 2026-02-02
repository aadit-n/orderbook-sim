# orderbookSim

Order book simulation engine with a C++ matching core and a Python runner. It generates synthetic order flow, matches orders, tracks trades, and computes portfolio P&L for user-submitted orders.

**Try it out here - [https://orderbooksimulator.streamlit.app](https://orderbooksimulator.streamlit.app)**

## Repository structure

- `src/main.py`: Python runner that loads the native library, generates orders, submits user orders, and computes analytics.
- `src/order.cpp`: Random order generation (price/size/type distributions and tick rounding).
- `src/orderbook.cpp`: Matching engine (price-time priority, execution price, expiry handling).
- `src/wrapper.cpp`: C ABI for the Python `ctypes` bindings.
- `include/order.h`: Order model.
- `include/orderbook.h`: Order book model and trade record structure.
- `requirements.txt`: Python dependencies.
- `setup.sh`, `packages.txt`: Build the native library on Linux hosts.

## How it works (end-to-end)

1. A native `OrderBook` is created in C++.
2. A background loop generates random orders and submits them to the book.
3. The matching engine executes trades and stores them as trade records.
4. Orders can also be submitted manually (user orders).
5. Trades are used to compute portfolio P&L and per-order realized P&L.
6. Order book snapshots and trade snapshots are periodically pulled into Python for metrics.

## Build and run

### Local build (Windows)
```powershell
mkdir build
g++ -shared -o build/orderbook.dll src/order.cpp src/orderbook.cpp src/wrapper.cpp -Iinclude -std=c++17
```

### Local build (Linux)
```bash
mkdir -p build
g++ -shared -fPIC -o build/orderbook.so src/order.cpp src/orderbook.cpp src/wrapper.cpp -Iinclude -std=c++17
```

### Local run
```bash
streamlit run src/main.py
```

### Streamlit Cloud
- `packages.txt` installs `g++`.
- `setup.sh` builds `build/orderbook.so` during deploy.
- `main.py` will also compile the library at runtime if it is missing.

## C++ core details

### Order model
`order` fields:
- `id`: unique order id.
- `side`: `"buy"` or `"sell"`.
- `quantity`: integer size.
- `price`: float (tick-rounded).
- `time`: submission time.
- `expiry`: 0 for GTC, otherwise UNIX timestamp.
- `type`: `"limit"` or `"market"`.
- `status`: `"open"`, `"closed"`, `"expired"`, `"cancelled"`.

### Matching logic
- **Price-time priority:** Orders are sorted by price. New orders at the same price are appended after existing ones (FIFO at that price).
- **Execution price:** Trades execute at the resting (book) price.
- **Market orders:** Execute against the book until exhausted; any remaining quantity is discarded.
- **Expiry:** Orders with `expiry > 0` are removed when expired; GTC orders use `expiry = 0`.

### Trade record model
Each execution generates a trade record:
- `trade_id`, `order_id`, `side`, `price`, `quantity`, `time`.
These are stored in `OrderBook::trades` and are used for P&L and analytics.

## Random order generation

Random orders are created in `randomOrder` with the following behavior:
- **Side:** 50/50 buy or sell.
- **Price:** anchored to a reference price, offset by a normal distribution (sigma configurable), then snapped to a tick size.
- **Size:** log-normal distribution (heavy-tailed), clamped between min/max.
- **Type:** market probability configurable; otherwise limit.
- **Expiry:** optional; default is GTC (no expiry).

The reference price can be set to a fixed base price or the live mid-price.

## Configuration options (sidebar controls)

These controls tune the simulation and analytics:

### Simulation
- **Orders per tick**: Number of random orders generated every simulation loop.
- **UI refresh (ms)**: Refresh rate for analytics and tables.
- **Metrics update cadence (ticks)**: How often derived metrics (spread, OBI, VWAP, etc.) are recomputed.
- **Row limit for table styling**: Disables expensive styling above this row count.

### Price/flow model
- **Base Price**: Reference price used when mid anchoring is off.
- **Anchor random prices to mid**: If enabled and both sides exist, reference price becomes the mid-price.
- **Tick Size**: Minimum price increment; all prices are snapped to this.
- **Price Sigma**: Standard deviation for price offsets around the reference price.
- **Market Order %**: Probability that a random order is a market order.
- **Expiry Seconds (0 = GTC)**: Expiry duration for random orders; 0 means no expiry.
- **Min Qty / Max Qty**: Clamp range for random order size.

### Manual orders
- **Side**: Buy or sell.
- **Quantity**: Order size.
- **Price**: Limit price (ignored for market orders).
- **Type**: Limit or market.

## Market metrics (definitions)

Computed from the live book:
- **Best Bid**: Highest buy price in the book.
- **Best Ask**: Lowest sell price in the book.
- **Midprice**: `(Best Bid + Best Ask) / 2`.
- **OBI (Order Book Imbalance)**: `(Best Bid - Best Ask) / (Best Bid + Best Ask)`.  
  Note: this is a price-based imbalance, not size-based.
- **Relative Spread**: `(Best Ask - Best Bid) / Midprice`.
- **Depth Bid**: Total buy quantity across all bid levels.
- **Depth Ask**: Total sell quantity across all ask levels.
- **VWAP Bid**: Volume-weighted average bid price across the book.
- **VWAP Ask**: Volume-weighted average ask price across the book.
- **OFI (Order Flow Imbalance)**: `BestBid * BestBidQty - BestAsk * BestAskQty` using the top of book.
- **Queue Pressure**: `BestBidQty / TotalBidDepth` (top-level queue concentration).
- **Microprice**:  
  `(BestAsk * BestBidQty + BestBid * BestAskQty) / (BestBidQty + BestAskQty)`

## Trades vs order events

- **Trades** are executions generated by matching; each trade is a single fill.
- **Order events** are non-trade outcomes for orders (expired, cancelled).  
  These are stored separately from trades.

## Portfolio and P&L

User orders are tracked in Python and matched against trades:
- **Cash**: Starting cash minus buy fills plus sell fills.
- **Position Qty**: Net filled quantity.
- **Average Cost**: Weighted average price of the current position.
- **Realized P&L**: Profit/loss from sell fills vs average cost at the time of fill.
- **Unrealized P&L**: `(Last Trade Price - Average Cost) * Position Qty`.
- **Total P&L**: `Realized + Unrealized`.

Per-order table fields:
- **ORDER_QTY / ORDER_PRICE**: Original order details.
- **FILLED_QTY / AVG_FILL_PRICE**: Aggregated fill stats from trades.
- **REMAINING**: `ORDER_QTY - FILLED_QTY`.
- **STATUS**: `open`, `partially_filled`, `filled`.
- **REALIZED_PNL**: Realized P&L attributed to sell orders only.

**All UI is AI generated**
