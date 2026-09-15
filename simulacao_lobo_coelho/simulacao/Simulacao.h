#pragma onde
#include "dominio/Mundo.h"

#include <random>
#include <cmath>
#include <chrono>
#include <cstddef>
#include <cstdint>

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

		void gerar_plantas();
		void processar_animais();
		double probabilidade_nascimento_planta;

		void tick_atualizar();
};
