#pragma once
#include <vector>
#include <cstddef>

#include "dominio/Celula.h"
#include "dominio/Tipos.h"

class Tabuleiro{
public:
	Tabuleiro(std::size_t linhas, std::size_t colunas);

	bool posicao_valida(Posicao posicao) const;

	Celula& obter(Posicao posicao);
	const Celula& obter(Posicao posicao) const; 

	std::size_t get_linhas() const;
	std::size_t get_colunas() const;
private:

	std::vector<std::vector<Celula>> celulas;

};