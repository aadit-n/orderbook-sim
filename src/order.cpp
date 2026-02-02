#include <iostream>
#include <algorithm>
#include <ctime>
#include <random>
#include <chrono>
#include "order.h"
#include "orderbook.h"
using namespace std;

order randomOrder(int &nextID, float basePrice){
    static thread_local mt19937 generator(random_device{}());
    normal_distribution<float> price(basePrice, 5);
    order newOrder;
    newOrder.id = nextID++;
    string side;
    int randint = rand()%2;
    if (randint == 0){
        side = "buy";
    }   
    else{
        side = "sell";
    }
    newOrder.side = side;
    newOrder.quantity = rand()%100+1;
    newOrder.price = max(1, int(price(generator)));
    newOrder.time = time(0);
    newOrder.expiry = newOrder.time+(rand()%11+5);
    string type;
    int randint2 = rand()%3;
    if (randint2==0||randint2==1){
        type = "limit";
    }
    else if (randint2==2){
        type = "market";
    }
    newOrder.type = type;
    newOrder.status = "open";

    return newOrder;
}

