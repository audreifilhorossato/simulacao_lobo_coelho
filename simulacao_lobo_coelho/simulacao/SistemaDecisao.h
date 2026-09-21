#pragma once 

#include "dominio/Animal.h"
#include "dominio/SistemaVisao.h"

#include <random>
#include<map>
#include <cmath>


class SistemaDecisao {
	public:
		Acao decidir(
			const Animal& animal,
			const VisaoAnimal& visaoanimal,
			std::mt19937& gerador
		) const;
	private:
		int direcao_mais_proxima_vetor_direcao(const Vec2 vetor_direcao, const std::vector<Vec2> destinos_possiveis) const;
		Acao decidir_coelho(
			const Animal& coelho,
			const VisaoAnimal& visao,
			std::mt19937& gerador
		) const;
};