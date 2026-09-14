#include "simulacao/Simulacao.h"


Simulacao::Simulacao(std::size_t linhas, std::size_t colunas) 
	:mundo(linhas, colunas), 
	tempo_acumulado(0.0), 
	tick_duracao(0.5), 
	tick_numero(0),
	gerador(1), //semente fixa por enquanto
	probabilidade_nascimento_planta(0.001) {
}

const Mundo& Simulacao::get_mundo() const{
	return mundo;
}

std::uint64_t Simulacao::get_numero_tick() const
{
	return tick_numero;
}

void Simulacao::tempo_avancar(Duracao tempo_passado) {
	const Duracao tempo_max(1.0);

	if (tempo_passado > tempo_max) {
		tempo_passado = tempo_max;
	}
	tempo_acumulado += tempo_passado;

	while (tempo_acumulado >= tick_duracao) {
		tick_atualizar();
		tempo_acumulado -= tick_duracao;
	}
}

void Simulacao::tick_atualizar(){
	gerar_plantas();
	++tick_numero;
}

void Simulacao::gerar_plantas() {
	const Tabuleiro& tabuleiro = mundo.get_tabuleiro();
	const int n_linhas = static_cast<int>(tabuleiro.get_linhas());
	const int n_colunas = static_cast<int>(tabuleiro.get_colunas());

	const int n_total_celulas = n_linhas * n_colunas;

	if (n_total_celulas == 0) {
		return;
	}

	int id_celula = -1;

	const double p_falha = std::log(1 - probabilidade_nascimento_planta);

	std::uniform_real_distribution<double> distribuicao(0.0,1.0);

	while (true) {
		const double u = distribuicao(gerador);
		
		const int salto = static_cast<int>(std::floor(std::log(1 - u) / p_falha)) + 1;

		id_celula += salto;

		if (id_celula >= n_total_celulas){
			break;
		}

		const int linha = id_celula / n_colunas;
		const int coluna = id_celula % n_colunas;

		mundo.adicionar_planta({ linha,coluna });

	}



}

