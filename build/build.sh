#!/bin/bash

echo "Building shared library for Linux/macOS..."

mkdir -p build

g++ -std=c++17 -O2 -static-libgcc -static-libstdc++ -fPIC -Iinclude \
    src/order.cpp src/orderbook.cpp src/wrapper.cpp \
    -shared -o build/liborderbook.so

echo "======================================="
echo "Build complete: build/orderbook.so"
echo "======================================="