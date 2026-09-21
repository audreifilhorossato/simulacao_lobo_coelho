#pragma once

/**
 * @brief Representa um animal na simulação.
 *
 * Um Animal possui identificador, espécie, posição no ambiente, energia
 * e um indicador de estado de vida. A classe é responsável
 * por armazenar esses atributos e expor operações básicas de consulta
 * e manutenção.
 */

#include "dominio/Tipos.h"

class Animal {
	public:
		/**
		 * @brief Constrói um novo Animal.
		 *
		 * @param id Identificador único do animal.
		 * @param especie Espécie à qual o animal pertence.
		 * @param posicao Posição inicial do animal no ambiente.
		 * @param energia_inicial Quantidade de energia com que o animal nasce.
		 * @param tick_nascimento Tick da simulação em que o animal nasceu.
		 */
		Animal(
			AnimalId id,
			Especie especie,
			Posicao posicao,
			int energia_inicial,
			Tick tick_nascimento
		);

		/// Retorna o identificador único do animal.
		AnimalId get_id() const;

		// Retorna a espécie do animal.
		Especie get_especie() const;

		/// Retorna a posição atual do animal no ambiente.
		Posicao get_posicao() const;

		/// Retorna o tick da simulação em que o animal nasceu.
		Tick get_nascimento() const;

		/**
		 * @brief Calcula a idade do animal em ticks.
		 *
		 * @param tick_atual Tick atual da simulação.
		 * @return Diferença entre @p tick_atual e o tick de nascimento,
		 *         ou 0 caso @p tick_atual seja anterior ou igual ao
		 *         nascimento, evitando idade negativa.
		 */
		Tick get_idade(Tick tick_atual) const;

		/// Retorna a quantidade atual de energia do animal.
		int get_energia() const;

		/// Retorna o tempo (em ticks) acumulado desde a última reprodução.
		int get_tempo_reproducao() const;

		/// Indica se o animal está vivo.
		bool get_vivo() const;

		/// Indica se o animal está sem energia (energia <= 0).
		bool esta_sem_energia() const;

		/**
		 * @brief Reduz a energia do animal.
		 *
		 * @param gasto quantidade de energia a ser subtraída.
		 * @note Não há verificação de limite inferior aqui;
		 */
		void gastar_energia(int gasto);

		/**
		 * @brief Aumenta a energia do animal.
		 *
		 * @param ganho Quantidade de energia a ser somada.
		 * @note Não há limite superior (cap) aplicado à energia.
		 */
		void ganhar_energia(int ganho);

		/**
		 * @brief Alterna o estado de vida do animal (vivo <-> morto).
		 */
		void alterar_vivo();

		/**
		 * @brief Atualiza a posição do animal.
		 *
		 * @param nova_posicao Nova posição a ser atribuída ao animal.
		 */
		void definir_posicao(Posicao nova_posicao);

	private:
		AnimalId id;			///< Identificador único do animal.
		Especie especie;		///< Espécie do animal.
		Posicao posicao;		///< Posição atual no ambiente.
		Tick tick_nascimento;	///< Tick em que o animal nasceu.

		int tempo_reproducao;	///< Ticks acumulados desde a última reprodução.
		int energia;			///< Energia atual do animal.
		bool vivo;				///< Estado de vida do animal (true = vivo).
};