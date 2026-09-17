#pragma once

#include "dominio/Tipos.h"

class Animal {
	public:
		Animal(
			AnimalId id,
			Especie especie,
			Posicao posicao,
			int energia_inicial,
			Tick tick_nascimento
		);

		AnimalId get_id() const;
		Especie get_especie() const;

		Posicao get_posicao() const;

		Tick get_nascimento() const;
		Tick get_idade(Tick tick_atual) const;

		int get_energia() const;
		int get_tempo_reproducao() const;

		bool get_vivo() const;
		bool esta_sem_energia() const;

		void gastar_energia(int gasto);
		void ganhar_energia(int ganho);
		void alterar_vivo();

		void definir_posicao(Posicao nova_posicao);

	private:
		AnimalId id;
		Especie especie;
		Posicao posicao;
		Tick tick_nascimento;
		Tick idade;

		int tempo_reproducao;
		int energia;
		bool vivo;
};