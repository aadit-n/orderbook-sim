#!/bin/bash

echo "Building shared library for Linux/macOS..."

mkdir -p build

g++ -shared -Iinclude -fPIC -o build/orderbook.dll src/order.cpp src/orderbook.cpp src/wrapper.cpp

echo "======================================="
echo "Build complete: build/orderbook.so"
echo "======================================="
