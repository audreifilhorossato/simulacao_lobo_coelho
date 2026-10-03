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
    std::mt19937& gerador,
    const int numero_tick
) const
{
    std::vector<Vec2> direcoes_possiveis;
    std::vector<Posicao> destinos_possiveis;


    std::uniform_int_distribution<int> chance(0, 100);
    const int percentagem = chance(gerador);

    if (visao.celula_central.tem_planta) {
        return{
            TipoAcao::Comer,
            coelho.get_id(),
            coelho.get_posicao()
        };
    }

    Vec2 vetor_direcao = {0.0, 0.0};

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

        if (celula.tem_carcaca && (celula.dist_quadrada > 0)) {
            vetor_direcao = vetor_direcao - (vetor_celula * (1.0 / celula.dist_quadrada));
        }

        if (celula.especie_animal.has_value() && celula.especie_animal.value() == Especie::Lobo) {
			vetor_direcao = vetor_direcao - (vetor_celula * (1.0 / celula.dist_quadrada)*2.0);
		}

        if ((celula.dist_quadrada <= 2) && (!celula.animal_id.has_value())) {
            direcoes_possiveis.push_back(vetor_celula);
            destinos_possiveis.push_back(celula.posicao);
        }
    }

    if (direcoes_possiveis.empty()) {
        return { TipoAcao::Esperar, coelho.get_id(), coelho.get_posicao() };
    }

    std::uniform_int_distribution<int> dist_int(0, destinos_possiveis.size() - 1);

    if (coelho.get_energia() > 50 && percentagem > 90 && coelho.get_idade(numero_tick) > IDADE_MAX_COELHO/6) {
        return{ TipoAcao::Reproduzir, coelho.get_id(), destinos_possiveis.at(dist_int(gerador)) };
    }

    const double eps = 1e-9;
    if ((
        (vetor_direcao.x == 0.0) && (vetor_direcao.y == 0.0)) || 
        (std::abs(vetor_direcao.x) < eps && std::abs(vetor_direcao.y) < eps
    )) {  
        if (percentagem < 60) {
      
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

Acao SistemaDecisao::decidir_lobo(
    const Animal& lobo,
    const VisaoAnimal& visao,
    std::mt19937& gerador,
    const int numero_tick
) const
{
    std::vector<Vec2> direcoes_possiveis;
    std::vector<Posicao> destinos_possiveis;
	std::vector<Posicao> alvo_possiveis;


    std::uniform_int_distribution<int> chance(0, 100);
    const int percentagem = chance(gerador);

    if (visao.celula_central.carcacaId.has_value()) {
        return{
            TipoAcao::Comer,
            lobo.get_id(),
            lobo.get_posicao()
        };
    }

    Vec2 vetor_direcao = { 0.0, 0.0 };

    for (const CelulaObservada& celula : visao.celulas) {

        Vec2 vetor_celula = {
                static_cast<double>(celula.posicao_relativa.linha),
                static_cast<double>(celula.posicao_relativa.coluna)
        };

        if (!celula.existe) {
            continue;
        }

        if (celula.tem_carcaca && (celula.dist_quadrada > 0)) {
            vetor_direcao = vetor_direcao + (vetor_celula * (1.0 / celula.dist_quadrada) * 3.0);
        }

        if (celula.especie_animal.has_value() && celula.especie_animal.value() == Especie::Coelho) {
            vetor_direcao = vetor_direcao + (vetor_celula * (1.0 / celula.dist_quadrada));
            if (celula.dist_quadrada <= 2) {
                alvo_possiveis.push_back(celula.posicao);
            }
        }

        if ((celula.dist_quadrada <= 2) && ((!celula.animal_id.has_value()) || (celula.tem_carcaca))) {
            direcoes_possiveis.push_back(vetor_celula);
            destinos_possiveis.push_back(celula.posicao);
        }
    }

    if (direcoes_possiveis.empty()) {
        return { TipoAcao::Esperar, lobo.get_id(), lobo.get_posicao() };
    }

    

	if (!alvo_possiveis.empty() && percentagem < 70) {
		std::uniform_int_distribution<int> dist_alvo(0, alvo_possiveis.size() - 1);
		return {
			TipoAcao::Matar,
			lobo.get_id(),
			alvo_possiveis.at(dist_alvo(gerador))
		};
	}

    std::uniform_int_distribution<int> dist_int(0, destinos_possiveis.size() - 1);

    if (lobo.get_energia() > 50 && percentagem > 90 && lobo.get_idade(numero_tick) > IDADE_MAX_LOBO / 4) {
        return{ TipoAcao::Reproduzir, lobo.get_id(), destinos_possiveis.at(dist_int(gerador)) };
    }

    const double eps = 1e-9;
    if ((
        (vetor_direcao.x == 0.0) && (vetor_direcao.y == 0.0)) ||
        (std::abs(vetor_direcao.x) < eps && std::abs(vetor_direcao.y) < eps
            )) {
        if (percentagem < 60) {

            return {
                TipoAcao::Mover,
                lobo.get_id(),
                destinos_possiveis.at(dist_int(gerador))
            };
        }
        else {
            return {
                TipoAcao::Esperar,
                lobo.get_id(),
                lobo.get_posicao()
            };
        }
    }


    const int indice = direcao_mais_proxima_vetor_direcao(vetor_direcao, direcoes_possiveis);

    if (indice < 0) {
        return { TipoAcao::Esperar, lobo.get_id(), lobo.get_posicao() };
    }

    return {
        TipoAcao::Mover,
        lobo.get_id(),
        destinos_possiveis.at(indice)
    };

}

Acao SistemaDecisao::decidir(
    const Animal& animal,
    const VisaoAnimal& visao,
    std::mt19937& gerador,
    const int numero_tick
) const {
    if (animal.get_especie() == Especie::Coelho)
    {
        return decidir_coelho(animal, visao, gerador,numero_tick);
    }
	else if (animal.get_especie() == Especie::Lobo)
	{
		return decidir_lobo(animal, visao, gerador, numero_tick);
	}

    return {
        TipoAcao::Esperar,
        animal.get_id(),
        animal.get_posicao()
    };
}
