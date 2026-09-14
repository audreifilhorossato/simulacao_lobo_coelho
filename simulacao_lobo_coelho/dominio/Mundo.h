#pragma once
#include "dominio/Tabuleiro.h"

class Mundo {
	public:
		Mundo(std::size_t linhas, std::size_t colunas);

		const Tabuleiro& get_tabuleiro() const;

		bool adicionar_planta(Posicao posicao);

	private:
		Tabuleiro tabuleiro;
};