#pragma once

#include "dominio/Tipos.h"
#include "dominio/Celula.h"

#include <optional>
#include <vector>
#include <cstdlib>

/**
 * @brief Representa uma célula observada dentro do campo de visão de um animal.
 *
 * Além das informações equivalentes às de uma Celula (presença de planta e
 * de animal), guarda a posição absoluta da célula no ambiente, sua posição
 * relativa ao animal observador, e um indicador de que a célula existe de
 * fato (por exemplo, para descartar posições fora dos limites do ambiente).
 */
struct CelulaObservada{
	Posicao posicao{ 0,0 };				///< Posição absoluta da célula observada no tabuleiro.
	Posicao posicao_relativa{ 0,0 };	///< Posição da célula relativa ao animal observador.

	bool existe = false;
	bool tem_planta = false;

	std::optional<AnimalId> animal_id = std::nullopt;		///< Identificador do animal presente na célula observada, se houver.
	std::optional<Especie> especie_animal = std::nullopt;	///< Espécie do animal presente na célula observada, se houver.
};

/**
 * @brief Representa o campo de visão de um animal em um dado tick da simulação.
 *
 * Contém a posição central a partir da qual a visão é calculada, a célula
 * central propriamente dita (onde o animal observador se encontra) e a
 * lista de células observadas dentro do alcance de visão do animal.
 */
struct VisaoAnimal{
	Posicao centro{ 0, 0 };					///< Posição central da visão, mesma do animal observador
	Celula celula_central;					///< Célula do animal observador
	std::vector<CelulaObservada> celulas;	///< Conjunto de células observadas dentro do alcance de visão do animal.
};