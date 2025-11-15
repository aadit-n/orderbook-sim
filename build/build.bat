@echo off
echo Building orderbook.dll...

if not exist build mkdir build

g++ -std=c++17 -O2 -static-libgcc -static-libstdc++ -Iinclude ^
    src/order.cpp src/orderbook.cpp src/wrapper.cpp ^
    -shared -o build\orderbook.dll

echo =======================================
echo Build complete: build\orderbook.dll
echo ======================================= 