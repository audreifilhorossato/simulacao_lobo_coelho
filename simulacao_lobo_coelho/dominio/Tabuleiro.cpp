
#include "dominio/Tabuleiro.h"
#include <stdexcept>

Tabuleiro::Tabuleiro(
    std::size_t linhas,
    std::size_t colunas
)
    :celulas(
        linhas,
        std::vector<Celula>(colunas)
    )
{
}

Posicao Tabuleiro::normatizar_posicao(Posicao posicao) const {
    const int n_linhas = static_cast<int>(get_linhas());
    const int n_colunas = static_cast<int>(get_colunas());

    if (n_colunas <= 0 || n_linhas <= 0) {
        throw std::logic_error("Nao e possivel normalizar em um tabuleiro vazio");
    }

    const int linha_norm = ((posicao.linha % n_linhas) + n_linhas) % n_linhas;
    const int coluna_norm = ((posicao.coluna % n_colunas) + n_colunas) % n_colunas;

    return { linha_norm, coluna_norm };

}



bool Tabuleiro::posicao_valida(Posicao posicao) const {
    // Primeiro verifica se a posição não é negativa.
    if (posicao.linha < 0 || posicao.coluna < 0) {
        return false;
    }

    // Depois verifica se não ultrapassa o tabuleiro.

    if (static_cast<std::size_t>(posicao.linha) < get_linhas() && static_cast<std::size_t>(posicao.coluna) < get_colunas()) {
        return true;
    }
    else
    {
        return false;
    }
}

Celula& Tabuleiro::obter(Posicao posicao) {
    if (!posicao_valida(posicao)) {
        throw std::out_of_range("Posicao fora do tabuleiro");
    }

    return celulas.at(static_cast<std::size_t>(posicao.linha)).at(static_cast<std::size_t>(posicao.coluna));
}

const Celula& Tabuleiro::obter(Posicao posicao) const {
    if (!posicao_valida(posicao)) {
        throw std::out_of_range("Posicao fora do tabuleiro");
    }

    return celulas.at(static_cast<std::size_t>(posicao.linha)).at(static_cast<std::size_t>(posicao.coluna));
}


std::size_t Tabuleiro::get_colunas() const {
    if (celulas.empty()) {
        return 0;
    }
    return celulas.at(0).size();
}

std::size_t Tabuleiro::get_linhas() const {
    return celulas.size();
}