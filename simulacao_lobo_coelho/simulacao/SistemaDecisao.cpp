#include "simulacao/SistemaDecisao.h"

int SistemaDecisao::direcao_mais_proxima_vetor_direcao(const Vec2 vetor_direcao, const std::vector<Vec2> direcoes_possiveis) const{
    int melhor_indice = -1;
    double menor_angulo = std::numeric_limits<double>::max();

    for (size_t i = 0; i < direcoes_possiveis.size(); ++i) {
        const Vec2& d = direcoes_possiveis[i];
        if (d.x == 0.0 && d.y == 0.0) continue;

        double cruz = vetor_direcao.x * d.y - vetor_direcao.y * d.x;
        double prod = vetor_direcao.x * d.x + vetor_direcao.y * d.y;
        double angulo = std::atan2(std::abs(cruz), prod);

        if (angulo < menor_angulo) {
            menor_angulo = angulo;
            melhor_indice = static_cast<int>(i);
        }
    }
    return melhor_indice;
}


Acao SistemaDecisao::decidir_coelho(
    const Animal& coelho,
    const VisaoAnimal& visao,
    std::mt19937& gerador
) const
{
    std::vector<Vec2> direcoes_possiveis;
    std::vector<Posicao> destinos_possiveis;

    if (visao.celula_central.tem_planta) {
        return{
            TipoAcao::Comer,
            coelho.get_id(),
            coelho.get_posicao()
        };
    }

    Vec2 vetor_direcao = { 0.0, 0.0};

    for (const CelulaObservada& celula : visao.celulas) {

        Vec2 vetor_celula = {
                static_cast<double>(celula.posicao_relativa.linha),
                static_cast<double>(celula.posicao_relativa.coluna)
        };

        if (!celula.existe) {
            continue;
        }

        if (celula.tem_planta && (celula.dist_quadrada > 0)) {
            vetor_direcao = vetor_direcao + (vetor_celula * (1.0/celula.dist_quadrada));
        }

        if ((celula.dist_quadrada <= 2) && (!celula.animal_id.has_value())) {
            direcoes_possiveis.push_back(vetor_celula);
            destinos_possiveis.push_back(celula.posicao);
        }
    }

    if (direcoes_possiveis.empty()) {
        return { TipoAcao::Esperar, coelho.get_id(), coelho.get_posicao() };
    }

    const double eps = 1e-9;
    if ((
        (vetor_direcao.x == 0.0) && (vetor_direcao.y == 0.0)) || 
        (std::abs(vetor_direcao.x) < eps && std::abs(vetor_direcao.y) < eps
    )) {  

        std::bernoulli_distribution chance(0.6); //60% de ser True
        if (chance(gerador)) {
            std::uniform_int_distribution<int> dist_int(0, destinos_possiveis.size() - 1);
            return {
                TipoAcao::Mover,
                coelho.get_id(),
                destinos_possiveis.at(dist_int(gerador))
            };
        }
        else {
            return {
                TipoAcao::Esperar,
                coelho.get_id(),
                coelho.get_posicao()
            };
        }
    }

    // ruído: gira o vetor de direção
    const double ruido_max = 20.0 * std::acos(-1.0) / 180.0;
    std::uniform_real_distribution<double> ruido(-ruido_max, ruido_max);
    const double a = ruido(gerador);
    const double c = std::cos(a);
    const double s = std::sin(a);
    vetor_direcao = {
        vetor_direcao.x * c - vetor_direcao.y * s,
        vetor_direcao.x * s + vetor_direcao.y * c
    };


    const int indice = direcao_mais_proxima_vetor_direcao(vetor_direcao, direcoes_possiveis);

    if (indice < 0) {
        return { TipoAcao::Esperar, coelho.get_id(), coelho.get_posicao() };
    }

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
