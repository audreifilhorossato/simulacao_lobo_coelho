#pragma once

#include "dominio/Tipos.h"

#include <optional>
#include <vector>

struct CelulaObservada{
	Posicao posicao{ 0,0 };
	Posicao posicao_relativa{ 0,0 };

	bool existe = false;
	bool tem_planta = false;

	std::optional<AnimalId> animal_id = std::nullopt;
	std::optional<Especie> especie_animal = std::nullopt;
};

struct VisaoAnimal{
	Posicao centro{ 0, 0 };
	std::vector<CelulaObservada> celulas;
};