#pragma once

/**
 * @brief Representa uma célula do ambiente (grade) da simulação.
 *
 * Cada célula pode conter uma planta e/ou estar ocupada por, no máximo,
 * um animal. A ausência de animal na célula é representada por
 * animalId igual a std::nullopt.
 */

#include <optional>
#include "dominio/Tipos.h"

struct Celula{
	bool tem_planta = false;							///< Indica se há uma planta disponível na célula.
	std::optional<AnimalId> animalId = std::nullopt;	///< Identificador do animal que ocupa a célula, ou std::nullopt se estiver vazia.
};