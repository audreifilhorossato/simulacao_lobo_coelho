#include "simulacao/SistemaDecisao.h"


Acao SistemaDecisao::decidir_coelho(
    const Animal& coelho,
    const VisaoAnimal& visao,
    std::mt19937& gerador
) const
{
    std::vector<Posicao> destinos_possiveis;

    for (const CelulaObservada& celula : visao.celulas) {
        const float distancia_quadrada = (celula.posicao.coluna * celula.posicao.coluna) + (celula.posicao.linha) * (celula.posicao.linha);
        if (distancia_quadrada > 2) {
            continue;
        }
        if (!celula.existe) {
            continue;
        }
        if (celula.animal_id.has_value()) {
            continue;
        }
        destinos_possiveis.push_back(celula.posicao);
 
    }

    if (destinos_possiveis.empty()){
        return {
            TipoAcao::Esperar,
            coelho.get_id(),
            coelho.get_posicao()
        };
    }
    std::uniform_int_distribution<std::size_t> distribuicao (0,destinos_possiveis.size() - 1);

    const std::size_t indice = distribuicao(gerador);

    return {
        TipoAcao::Mover,
        coelho.get_id(),
        destinos_possiveis.at(indice)
    };

}

Acao SistemaDecisao::decidir(
    const Animal& animal,
    const VisaoAnimal& visao,
    std::mt19937& gerador
) const {
    if (animal.get_especie() == Especie::Coelho)
    {
        return decidir_coelho(animal, visao, gerador);
    }

    return {
        TipoAcao::Esperar,
        animal.get_id(),
        animal.get_posicao()
    };
}

Acao SistemaDecisao::decidir_coelho(
    const Animal& coelho,
    const VisaoAnimal& visao,
    std::mt19937& gerador
) const{
    return;
}
