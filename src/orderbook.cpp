#include <iostream>
#include <algorithm>
#include "order.h"
#include "orderbook.h"

using namespace std;

static void recordTrade(OrderBook &book, const order &o, int tradedQty) {
    if (tradedQty <= 0) return;
    order filled = o;
    filled.quantity = tradedQty;
    filled.status   = "closed";
    book.fulfilled.push_back(filled);
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

            recordTrade(book, newOrder, traded);
            recordTrade(book, *it,      traded);

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

            recordTrade(book, newOrder, traded);
            recordTrade(book, *it,      traded);

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
        bool inserted = false;

        if (book.buy.empty()) {
            book.buy.push_back(newOrder);
            inserted = true;
        } else {
            for (size_t i = 0; i < book.buy.size(); ++i) {
                if (newOrder.price > book.buy[i].price) {
                    book.buy.insert(book.buy.begin() + i, newOrder);
                    inserted = true;
                    break;
                }
            }
            if (!inserted) {
                book.buy.push_back(newOrder);
            }
        }
    } else { 
        bool inserted = false;

        if (book.sell.empty()) {
            book.sell.push_back(newOrder);
            inserted = true;
        } else {
            for (size_t i = 0; i < book.sell.size(); ++i) {
                if (newOrder.price < book.sell[i].price) {
                    book.sell.insert(book.sell.begin() + i, newOrder);
                    inserted = true;
                    break;
                }
            }
            if (!inserted) {
                book.sell.push_back(newOrder);
            }
        }
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
        if (it->expiry<=now){
            it->status = "expired";
            book.fulfilled.push_back(*it);
            it = book.buy.erase(it);
        }
        else{
            ++it;
        }
    }

    for (auto it = book.sell.begin(); it!=book.sell.end();){
        if (it ->expiry<=now){
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
