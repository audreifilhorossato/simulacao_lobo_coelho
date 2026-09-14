#pragma once
#include <optional>
#include "dominio/Tipos.h"


struct Celula{
	bool tem_planta = false;
	std::optional<AnimalId> animalId = std::nullopt;
};