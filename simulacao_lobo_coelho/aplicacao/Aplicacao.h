#pragma once

#include "interface/Interface.h"
#include "simulacao/Simulacao.h"

#include <chrono>
class Aplicacao {
	public:
		Aplicacao();

		void executar();
	private:
		Simulacao simulacao;
		Interface interface;
};