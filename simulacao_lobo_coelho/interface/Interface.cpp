#include "Interface.h"

Interface::Interface(std::size_t linhas, std::size_t colunas, float tamanho_celula)
    : LINHAS(linhas),
    COLUNAS(colunas),
    TAMANHO_CELULA(tamanho_celula),
    janela(
        sf::VideoMode({
            static_cast<unsigned int>(COLUNAS * TAMANHO_CELULA),
            static_cast<unsigned int>(LINHAS * TAMANHO_CELULA)
        }),
        "Simulacao de Ecossistema",
        sf::Style::Titlebar | sf::Style::Close
    )
{
    janela.setFramerateLimit(60);
}

bool Interface::esta_aberta() const
{
    return janela.isOpen();
}

void Interface::processar_eventos() {
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

void Interface::desenhar(const Mundo& mundo) {
    janela.clear(sf::Color(25, 25, 25));

    const Tabuleiro& tabuleiro = mundo.get_tabuleiro();

    sf::RectangleShape quadrado({
        TAMANHO_CELULA - 1.0f,
        TAMANHO_CELULA - 1.0f
        });

    for (std::size_t linha = 0; linha < tabuleiro.get_linhas(); linha++) {
        for (std::size_t coluna = 0; coluna < tabuleiro.get_colunas(); coluna++) {
            Posicao posicao{
                static_cast<int>(linha),
                static_cast<int>(coluna)
            };

            const Celula& celula = tabuleiro.obter(posicao);


            //celula inicimente vazia
            sf::Color cor_celula = sf::Color(55, 90, 55);

            if (celula.animalId.has_value()) {
                const AnimalId id = celula.animalId.value();
                const Animal* animal = mundo.buscar_animal(id);

                if (animal == nullptr) {
                    //Problema a celula tem id que não existe animal
                    cor_celula = sf::Color(255, 0, 255);
                }
                else {
                    switch (animal->get_especie())
                    {
                        case Especie::Coelho:
                            cor_celula = sf::Color(240, 240, 240);
                            break;
                        case Especie::Lobo:
                            cor_celula = sf::Color(100, 100, 100);
                            break;
                    }
                }
            }
            else if (celula.tem_planta) {
                //planta
                cor_celula = sf::Color(40, 200, 60);
            }

            quadrado.setFillColor(cor_celula);

            float x = static_cast<float>(coluna) * TAMANHO_CELULA;
            float y = static_cast<float>(linha) * TAMANHO_CELULA;
            quadrado.setPosition({ x,y });
            janela.draw(quadrado);
        }
    }

    janela.display();
}



