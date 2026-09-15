#pragma once
#include "dominio/Tabuleiro.h"
#include "dominio/Tipos.h"
#include "dominio/Animal.h"
#include <unordered_map>

class Mundo {
	public:
		Mundo(std::size_t linhas, std::size_t colunas);

		std::optional<AnimalId> adicionar_animal(
			Especie especie,
			Posicao posicao,
			int energia_inicial,
			Tick tick_atual
		);
		void remover_animal(AnimalId id);

		// Ponteitero para poder retornar null
		const Animal* buscar_animal(AnimalId id) const;
		Animal* buscar_animal(AnimalId id);

		const Tabuleiro& get_tabuleiro() const;

		bool adicionar_planta(Posicao posicao);

		const std::unordered_map<AnimalId, Animal>& get_animais() const;

	private:
		Tabuleiro tabuleiro;
		std::unordered_map<AnimalId, Animal> animais;
		AnimalId proximo_id;
};