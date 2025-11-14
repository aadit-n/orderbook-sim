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

    void printOrder(){
        cout << "Order ID: " << id << "\n";
        cout << "Side: " << side << "\n";
        cout << "Quantity: " << quantity << "\n";
        cout << "Price: " << price << "\n";
        cout << "Time: " << ctime(&time) << "\n";
        cout << "Type: " << type << "\n";
        cout << "Status: " << status << "\n\n";
    }
};
order randomOrder(int &nextID, float basePrice);
order userGeneratedOrder(int &nextID, string side, int quantity, float price, string type);
#endif
