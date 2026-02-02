#!/usr/bin/env bash
set -e

mkdir -p build
g++ -shared -fPIC -o build/orderbook.so \
  src/order.cpp src/orderbook.cpp src/wrapper.cpp \
  -Iinclude -std=c++17