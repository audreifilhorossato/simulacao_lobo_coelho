#pragma once
#include "dominio/Mundo.h"
#include "simulacao/SistemaDecisao.h"

#include <random>
#include <cmath>
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <string>
#include <map>
#include <vector>
#include <utility>
#include <iostream>
#include <optional>
#include <deque>
#include <execution>
#include <algorithm>

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

		int linhas;
		int colunas;

		std::mt19937 gerador;
		SistemaDecisao sistema_decisao;

		std::uint64_t semente_base = 1;

		std::vector<Acao> resolver_conflitos(const std::vector<Acao>& acoes);
		void executar_acoes(const std::vector<Acao>& acoes);

		void gerar_plantas();
		void destruir_carcacas();
		void gerar_carcacas(const std::vector<AnimalId>& animais_mortos);
		std::vector<Acao> processar_animais();
		std::vector<AnimalId> matar_animais();
		double probabilidade_nascimento_planta;
		void setup_inicial();
		void tick_atualizar();

		std::vector<Acao> processar_animais_paralelo();
		static std::mt19937 gerador_paralelo(std::uint64_t semente, int tick, int id);

		template <typename F>
		static void paralelo_para(std::size_t n, F&& f) {
			if (n == 0) return;
			const std::size_t n_threads =
				std::min<std::size_t>(n, std::max(1u, std::thread::hardware_concurrency()));
			const std::size_t bloco_size = (n + n_threads - 1) / n_threads;

			std::vector<std::thread> threads;
			threads.reserve(n_threads);
			for (std::size_t t = 0; t < n_threads; ++t) {
				const std::size_t ini = t * bloco_size;
				const std::size_t fim = std::min(n, ini + bloco_size);
				if (ini >= fim) break;
				threads.emplace_back([&f, ini, fim] {
					for (std::size_t i = ini; i < fim; ++i) f(i);
					});
			}
			for (auto& thread : threads) thread.join();
		}
};
