#pragma once

/**
 * @brief Tipos básicos e estruturas de dados compartilhadas pelo domínio
 *        da simulação (identificadores, posição, espécies e ações).
 */

#include <cstdint>

 /// Identificador único de um animal na simulação.
using AnimalId = std::uint32_t;

/// Representa um instante (passo) discreto de tempo da simulação.
using Tick = std::uint64_t;

/**
 * @brief Representa uma posição no ambiente da simulação, dada por
 *        linha e coluna em uma grade.
 */
struct Posicao{
	int linha;
	int coluna;
};

/// Espécies de animais suportadas pela simulação.
enum class Especie{
	Coelho,
	Lobo
};

/// Tipos de ação que um animal pode executar em um tick da simulação.
enum class TipoAcao
{
	Esperar,
	Mover,
	Comer
};

/**
 * @brief Representa a ação escolhida por um animal em um tick da simulação.
 */
struct Acao
{
	TipoAcao tipo;			///< Tipo da ação a ser executada.
	AnimalId animal_id;		///< Identificador do animal que executa a ação.
	Posicao destino;		///< Posição de destino associada à ação (ex.: célula para onde mover ou da qual comer).
};