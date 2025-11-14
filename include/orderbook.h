#ifndef ORDERBOOK_H
#define ORDERBOOK_H
#include <iostream>
#include <vector>
#include <C:\Users\DEVELOPMENT\Desktop\coding projects\order_book\include\order.h>
using namespace std;

class OrderBook{
    public:
        vector<order> buy;
        vector<order> sell;
        vector<order> fulfilled; 
        
    void printOrderBook(){
        std::cout << "BID:\n";
        for (int i = 0; i < buy.size(); i++){
            buy[i].printOrder();
        }
        std::cout << "ASK:\n";
        for (int i = 0; i < sell.size(); i++){
            sell[i].printOrder();
        }
    }
};
void addOrder(OrderBook &book, order &newOrder);
void matchOrders(OrderBook &book, order &newOrder);
void cancelOrder(OrderBook &book, int orderID);
void orderExpiry(OrderBook &book);
#endif
