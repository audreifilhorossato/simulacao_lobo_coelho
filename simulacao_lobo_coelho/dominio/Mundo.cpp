#include "dominio/Mundo.h"

Mundo::Mundo(std::size_t linhas, std::size_t colunas) :tabuleiro(linhas, colunas){}

const Tabuleiro& Mundo::get_tabuleiro() const{
	return tabuleiro;
}

bool Mundo::adicionar_planta(Posicao posicao) {
	Celula& celula = tabuleiro.obter(posicao);
	if (celula.tem_planta) {
		return false;
	}
	celula.tem_planta = true;
	return true;
}