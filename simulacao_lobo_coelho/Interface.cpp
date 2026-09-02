#include "Interface.h"

Interface::Interface()
    : janela(
        sf::VideoMode({
            static_cast<unsigned int>(COLUNAS * TAMANHO_CELULA),
            static_cast<unsigned int>(LINHAS * TAMANHO_CELULA)
        }),
        "Simulacao de Ecossistema"
    )
{
    janela.setFramerateLimit(60);
}

void Interface::executar() {
    while (janela.isOpen()) {
        processarEventos();
        desenhar();
    }
}

void Interface::processarEventos() {
    std::optional<sf::Event> evento = janela.pollEvent();
    while (evento.has_value()) {
        if (evento.value().is<sf::Event::Closed>()) {
            janela.close();
        }

        const sf::Event::KeyPressed* ponteiroTecla = evento.value().getIf<sf::Event::KeyPressed>();

        if (ponteiroTecla != nullptr) {

            const sf::Event::KeyPressed& tecla = *ponteiroTecla;
            if (tecla.scancode == sf::Keyboard::Scancode::Escape){
                janela.close();
            }
            // Adicionar mais if para eventos de teclas 
        }
        evento = janela.pollEvent();
    }
}

void Interface::desenhar() {
    janela.clear(sf::Color(25, 25, 25));

    sf::RectangleShape celula({
        TAMANHO_CELULA - 1.0f,
        TAMANHO_CELULA - 1.0f
    });

    celula.setFillColor(sf::Color(55, 90, 55));

    for (unsigned int linha = 0; linha < LINHAS; ++linha) {
        for (unsigned int coluna = 0; coluna < COLUNAS; ++coluna) {
            celula.setPosition({
                coluna * TAMANHO_CELULA,
                linha * TAMANHO_CELULA
            });
            janela.draw(celula);
        }
    }
    // Adiciono outros elementos para serem desenhados a ordem importa

    janela.display();
}



