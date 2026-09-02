#pragma once

#include <SFML/Graphics.hpp>

class Interface {
    public:
        Interface();

        void executar();

    private:
        void processarEventos();
        void desenhar();

        static constexpr unsigned int COLUNAS = 30;
        static constexpr unsigned int LINHAS = 30;
        static constexpr float TAMANHO_CELULA = 40.0f;

        sf::RenderWindow janela;
};