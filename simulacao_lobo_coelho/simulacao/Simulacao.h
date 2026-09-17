#pragma onde
#include "dominio/Mundo.h"
#include "simulacao/SistemaDecisao.h"

#include <random>
#include <cmath>
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <string>
#include <map>
#include <optinal>

class Simulacao {
	public:
		Simulacao(std::size_t linhas, std::size_t colunas);

		using Duracao = std::chrono::duration<double>;

		void tempo_avancar(Duracao tempo_passado);

		const Mundo& get_mundo() const;

		const Tick get_tick_numero() const;

		std::uint64_t get_numero_tick() const;

	private:
		Mundo mundo;
		Duracao tempo_acumulado;
		Duracao tick_duracao;
		std::uint64_t tick_numero;

		std::mt19937 gerador;
		SistemaDecisao sistema_decisao;

		void resolver_conflitos(std::vector<Acao> acoes);
		void gerar_plantas();
		std::vector<Acao> processar_animais();
		void matar_animais();
		double probabilidade_nascimento_planta;

		void tick_atualizar();
};
