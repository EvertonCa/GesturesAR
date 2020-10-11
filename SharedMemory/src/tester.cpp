//
// Created by Everton Cardoso on 10/10/20.
//

#include <iostream>
#include <chrono>
#include <thread>

int main(){
    int contador = 1;
    while (true){
        std::cout << "ABCDEFGH" << std::endl;
        std::cout.flush();
        std::this_thread::sleep_for(std::chrono::milliseconds(33));
        contador++;
    }
}