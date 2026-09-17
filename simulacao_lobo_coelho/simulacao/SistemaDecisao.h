#pragma once 

#include "dominio/Acoes.h"
#include "dominio/Animal.h"
#include "dominio/SistemaVisao.h"

#include <random>
#include<map>

class SistemaDecisao {
	public:
		Acao decidir(
			const Animal& animal,
			const VisaoAnimal& visaoanimal,
			std::mt19937& gerador
		) const;
	private:
		Acao decidir_coelho(
			const Animal& coelho,
			const VisaoAnimal& visao,
			std::mt19937& gerador
		) const;
};