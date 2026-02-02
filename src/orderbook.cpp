#include <iostream>
#include <algorithm>
#include "order.h"
#include "orderbook.h"

using namespace std;

static void recordTrade(OrderBook &book, const order &o, int tradedQty, float execPrice) {
    if (tradedQty <= 0) return;
    OrderBook::Trade t;
    t.trade_id = book.next_trade_id++;
    t.order_id = o.id;
    t.side = o.side;
    t.price = execPrice;
    t.quantity = tradedQty;
    t.time = time(0);
    book.trades.push_back(t);
}


void matchOrders(OrderBook &book, order &newOrder) {
    orderExpiry(book);
    if (newOrder.quantity <= 0) return;

    if (newOrder.side == "buy") {
        for (auto it = book.sell.begin();
             it != book.sell.end() && newOrder.quantity > 0; ) {

            bool price_ok =
                (newOrder.type == "market") ||
                (newOrder.price >= it->price);

            if (!price_ok) {
                break;
            }

            int traded = min(newOrder.quantity, it->quantity);
            if (traded <= 0) {
                ++it;
                continue;
            }

            float exec_price = it->price;
            recordTrade(book, newOrder, traded, exec_price);
            recordTrade(book, *it,      traded, exec_price);

            newOrder.quantity -= traded;
            it->quantity      -= traded;

            //cout << "Traded quantity " << traded << "\n";

            if (it->quantity == 0) {
                it->status = "closed";
                it = book.sell.erase(it);
                //cout << "Resting sell order fully filled and removed\n";
            } else {
                ++it;
            }
        }
    } else { 
        for (auto it = book.buy.begin();
             it != book.buy.end() && newOrder.quantity > 0; ) {

            bool price_ok =
                (newOrder.type == "market") ||
                (newOrder.price <= it->price);

            if (!price_ok) {
                break;
            }

            int traded = min(newOrder.quantity, it->quantity);
            if (traded <= 0) {
                ++it;
                continue;
            }

            float exec_price = it->price;
            recordTrade(book, newOrder, traded, exec_price);
            recordTrade(book, *it,      traded, exec_price);

            newOrder.quantity -= traded;
            it->quantity      -= traded;

            //cout << "Traded quantity " << traded << "\n";

            if (it->quantity == 0) {
                it->status = "closed";
                it = book.buy.erase(it);
                //cout << "Resting buy order fully filled and removed\n";
            } else {
                ++it;
            }
        }
    }

    if (newOrder.type == "market") {
        if (newOrder.quantity > 0) {
            //cout << "Market order " << newOrder.id
              //   << " not fully filled, leftover " << newOrder.quantity
                // << " discarded\n";
        }
        newOrder.quantity = 0;
        newOrder.status   = "closed";
    }
}

void addOrder(OrderBook &book, order &newOrder) {
    orderExpiry(book);
    matchOrders(book, newOrder);

    if (newOrder.type == "market" || newOrder.quantity <= 0) {
        newOrder.status = "closed";
        return;
    }

    if (newOrder.side == "buy") {
        size_t i = 0;
        for (; i < book.buy.size(); ++i) {
            if (newOrder.price > book.buy[i].price) {
                break;
            }
        }
        for (; i < book.buy.size(); ++i) {
            if (newOrder.price != book.buy[i].price) {
                break;
            }
        }
        book.buy.insert(book.buy.begin() + i, newOrder);
    } else { 
        size_t i = 0;
        for (; i < book.sell.size(); ++i) {
            if (newOrder.price < book.sell[i].price) {
                break;
            }
        }
        for (; i < book.sell.size(); ++i) {
            if (newOrder.price != book.sell[i].price) {
                break;
            }
        }
        book.sell.insert(book.sell.begin() + i, newOrder);
    }
}

void cancelOrder(OrderBook &book, int orderID){
    for (auto it = book.buy.begin(); it!=book.buy.end();){
        if (it->id==orderID){
            it->status = "cancelled";
            book.fulfilled.push_back(*it);
            it = book.buy.erase(it);
        }
        else{
            ++it;
        }
    }
    for (auto it = book.sell.begin(); it!=book.sell.end();){
        if (it->id==orderID){
            it->status = "cancelled";
            book.fulfilled.push_back(*it);
            it = book.sell.erase(it);
        }
        else{
            ++it;
        }
    }
}

void orderExpiry(OrderBook &book){
    time_t now = time(0);
    for (auto it = book.buy.begin(); it!=book.buy.end();){
        if (it->expiry > 0 && it->expiry<=now){
            it->status = "expired";
            book.fulfilled.push_back(*it);
            it = book.buy.erase(it);
        }
        else{
            ++it;
        }
    }

    for (auto it = book.sell.begin(); it!=book.sell.end();){
        if (it->expiry > 0 && it->expiry<=now){
            it->status = "expired";
            it->quantity = 0;
            book.fulfilled.push_back(*it);
            it = book.sell.erase(it);
        }
        else{
            ++it;
        }   
    }
}
