#include <iostream>
#include <sstream>
#include <ctime>
#include "order.h"
#include "orderbook.h"
using namespace std;

extern "C"{
    OrderBook* creatBook(){
        return new OrderBook();
    }

    order* generate_random_order(int &nextID, float basePrice){
        return new order(randomOrder(nextID, basePrice));
    }

    void set_random_config(float tick_size,
                           float price_sigma,
                           float market_prob,
                           float cross_prob,
                           int expiry_seconds,
                           int min_qty,
                           int max_qty) {
        setRandomConfig(tick_size, price_sigma, market_prob, cross_prob, expiry_seconds, min_qty, max_qty);
    }

    void add_order(OrderBook* book, order* newOrder){
        addOrder(*book, *newOrder);
    }    


    const char* get_orderbook_snapshot(OrderBook* book) {
        static std::string snapshot;
        std::ostringstream ss;

        ss << "ID,SIDE,PRICE,QTY,TYPE\n";
        for (auto& o : book->buy)
            ss << o.id << ",BUY,"  << o.price << "," << o.quantity << "," << o.type << "\n";
        for (auto& o : book->sell)
            ss << o.id << ",SELL," << o.price << "," << o.quantity << "," << o.type << "\n";

        snapshot = ss.str();
        return snapshot.c_str();
    }

    const char* get_fulfilled_snapshot(OrderBook* book) {
        static std::string result;
        std::ostringstream oss;

        if (!book || book->fulfilled.empty()) {
            result = "";
            return result.c_str();
        }

        oss << "ID,SIDE,PRICE,QUANTITY,TYPE,STATUS\n";
        for (auto &o : book->fulfilled) {
            oss << o.id << ","
                << o.side << ","
                << o.price << ","
                << o.quantity << ","
                << o.type << ","
                << o.status << "\n";
        }

        result = oss.str();
        return result.c_str();
    }

    const char* get_trades_snapshot(OrderBook* book) {
        static std::string result;
        std::ostringstream oss;

        if (!book || book->trades.empty()) {
            result = "";
            return result.c_str();
        }

        oss << "TRADE_ID,ORDER_ID,SIDE,PRICE,QUANTITY,TIME\n";
        for (auto &t : book->trades) {
            oss << t.trade_id << ","
                << t.order_id << ","
                << t.side << ","
                << t.price << ","
                << t.quantity << ","
                << t.time << "\n";
        }

        result = oss.str();
        return result.c_str();
    }

    order* make_user_order(int id,
                        const char* side,
                        int quantity,
                        float price,
                        const char* type)
    {
        order* o = new order();
        o->id = id;
        o->side = std::string(side);
        o->quantity = quantity;
        o->price = price;
        o->time = std::time(nullptr);
        o->type = std::string(type);
        o->status = "open";
        return o;
    }

}
