#pragma once
#include "dominio/Tabuleiro.h"
#include "dominio/Tipos.h"
#include "dominio/SistemaVisao.h"
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
		bool remover_carcaca(AnimalId id);

		// Ponteitero para poder retornar null
		const Animal* buscar_animal(AnimalId id) const;
		Animal* buscar_animal(AnimalId id);

		const Tabuleiro& get_tabuleiro() const;

		bool remover_planta(Posicao posicao);
		bool adicionar_planta(Posicao posicao);
		std::optional<AnimalId> adicionar_carcaca(const Animal& animal_morto, Tick tick_numero);

		VisaoAnimal observar(Posicao centro,int raio) const;

		const std::unordered_map<AnimalId, Animal>& get_animais() const;

		bool mover_animal(AnimalId id, Posicao destino);

		const Carcaca* buscar_carcaca(AnimalId id) const;
		Carcaca* buscar_carcaca(AnimalId id);

		const std::unordered_map<AnimalId, Carcaca>& get_carcacas() const;

	private:
		Tabuleiro tabuleiro;
		std::unordered_map<AnimalId, Animal> animais;
		std::unordered_map<AnimalId, Carcaca> carcacas;
		AnimalId proximo_id;
		void criar_lago();
};