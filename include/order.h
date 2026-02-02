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
        int price;
        time_t time;
        time_t expiry;
        string type;
        string status;
        bool operator==(const order& rhs) const { return id == rhs.id; }
};
order randomOrder(int &nextID, float basePrice);
#endif
