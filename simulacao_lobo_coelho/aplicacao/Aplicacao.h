#pragma once

#include "interface/Interface.h"
#include "simulacao/Simulacao.h"

#include <chrono>
class Aplicacao {
	public:
		Aplicacao();

		void executar();
	private:
		const int tamanho_celula = 10;
		const int linhas = 80;
		const int colunas = 80;
		Simulacao simulacao;
		Interface interface;
};