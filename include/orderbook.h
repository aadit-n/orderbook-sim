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
};
void addOrder(OrderBook &book, order &newOrder);
void orderExpiry(OrderBook &book);
#endif
