#ifndef ORDER_H
#define ORDER_H
#include <iostream>
#include <string>
using namespace std;
class order{
    public:
        int id;
        string side;
        int quantity;
        float price;
        time_t time;
        time_t expiry;
        string type;
        string status;
        bool operator==(const order& rhs) const { return id == rhs.id; }
};
order randomOrder(int &nextID, float basePrice);
void setRandomConfig(float tick_size,
                     float price_sigma,
                     float market_prob,
                     float cross_prob,
                     int expiry_seconds,
                     int min_qty,
                     int max_qty);
#endif
