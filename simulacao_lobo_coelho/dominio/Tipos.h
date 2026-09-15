#pragma once
#include <cstdint>

using AnimalId = std::uint32_t;

using Tick = std::uint64_t;

struct Posicao{
	int linha;
	int coluna;
};

enum class Especie{
	Coelho,
	Lobo
};