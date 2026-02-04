#include <iostream>
#include <algorithm>
#include <ctime>
#include <random>
#include <chrono>
#include <cmath>
#include "order.h"
#include "orderbook.h"
using namespace std;

namespace {
    struct RandomConfig {
        float tick_size = 0.01f;
        float price_sigma = 1.5f;
        float market_prob = 0.1f;
        float cross_prob = 0.15f;
        int expiry_seconds = 0; // 0 = GTC
        int min_qty = 1;
        int max_qty = 200;
    };

    RandomConfig g_cfg;

    float snap_to_tick(float price, float tick) {
        if (tick <= 0.0f) return price;
        return roundf(price / tick) * tick;
    }

    int clamp_qty(int qty, int min_qty, int max_qty) {
        if (qty < min_qty) return min_qty;
        if (qty > max_qty) return max_qty;
        return qty;
    }
}

void setRandomConfig(float tick_size,
                     float price_sigma,
                     float market_prob,
                     float cross_prob,
                     int expiry_seconds,
                     int min_qty,
                     int max_qty) {
    if (tick_size > 0.0f) g_cfg.tick_size = tick_size;
    if (price_sigma > 0.0f) g_cfg.price_sigma = price_sigma;
    if (market_prob >= 0.0f && market_prob <= 1.0f) g_cfg.market_prob = market_prob;
    if (cross_prob >= 0.0f && cross_prob <= 1.0f) g_cfg.cross_prob = cross_prob;
    if (expiry_seconds >= 0) g_cfg.expiry_seconds = expiry_seconds;
    if (min_qty > 0) g_cfg.min_qty = min_qty;
    if (max_qty >= g_cfg.min_qty) g_cfg.max_qty = max_qty;
}

order randomOrder(int &nextID, float basePrice){
    static thread_local mt19937 generator(random_device{}());
    normal_distribution<float> price_dist(0.0f, g_cfg.price_sigma);
    lognormal_distribution<float> size_dist(3.0f, 0.6f);
    order newOrder;
    newOrder.id = nextID++;
    string side;
    int randint = rand()%2;
    side = (randint == 0) ? "buy" : "sell";
    newOrder.side = side;
    int qty = static_cast<int>(size_dist(generator));
    newOrder.quantity = clamp_qty(qty, g_cfg.min_qty, g_cfg.max_qty);

    float base = max(g_cfg.tick_size, basePrice);
    float offset = fabs(price_dist(generator));
    float r_cross = std::generate_canonical<float, 10>(generator);
    bool cross = r_cross < g_cfg.cross_prob;
    float raw_price;
    if (side == "buy") {
        raw_price = cross ? (base + offset) : (base - offset);
    } else {
        raw_price = cross ? (base - offset) : (base + offset);
    }
    float snapped = snap_to_tick(raw_price, g_cfg.tick_size);
    newOrder.price = max(g_cfg.tick_size, snapped);
    newOrder.time = time(0);
    if (g_cfg.expiry_seconds > 0) {
        newOrder.expiry = newOrder.time + g_cfg.expiry_seconds;
    } else {
        newOrder.expiry = 0;
    }

    float r = std::generate_canonical<float, 10>(generator);
    newOrder.type = (r < g_cfg.market_prob) ? "market" : "limit";
    newOrder.status = "open";

    return newOrder;
}

