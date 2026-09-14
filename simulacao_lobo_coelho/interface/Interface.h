#pragma once

#include <SFML/Graphics.hpp>
#include "dominio/Mundo.h"
#include <optional>

class Interface {
    public:
        Interface();
        void processar_eventos();
        bool esta_aberta() const;
        void desenhar(const Mundo& mundo);

    private:

        static constexpr unsigned int COLUNAS = 30;
        static constexpr unsigned int LINHAS = 30;
        static constexpr float TAMANHO_CELULA = 20.0f;

        sf::RenderWindow janela;
};