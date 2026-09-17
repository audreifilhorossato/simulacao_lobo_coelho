#pragma once

#include <SFML/Graphics.hpp>
#include "dominio/Mundo.h"
#include <optional>

class Interface {
    public:
        Interface(std::size_t linhas, std::size_t colunas, float tamanho_celula);
        void processar_eventos();
        bool esta_aberta() const;
        void desenhar(const Mundo& mundo);

    private:
        const float TAMANHO_CELULA;
        const int LINHAS;
        const int COLUNAS;
        sf::RenderWindow janela;
};