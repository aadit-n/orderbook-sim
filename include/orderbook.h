#ifndef ORDERBOOK_H
#define ORDERBOOK_H
#include <iostream>
#include <vector>
#include "order.h"
using namespace std;

class OrderBook{
    public:
        vector<order> buy;
        vector<order> sell;
        vector<order> fulfilled; 
        struct Trade {
            int trade_id;
            int order_id;
            string side;
            float price;
            int quantity;
            time_t time;
        };
        vector<Trade> trades;
        int next_trade_id = 1;

    OrderBook(){
        buy.reserve(1024);
        sell.reserve(1024);
        fulfilled.reserve(4096);
        trades.reserve(8192);
    }
};
void addOrder(OrderBook &book, order &newOrder);
void orderExpiry(OrderBook &book);
#endif
