#include "aplicacao/Aplicacao.h"

Aplicacao::Aplicacao():simulacao(30,30),interface(){};

void Aplicacao::executar() {
	using Relogio = std::chrono::steady_clock;
	Relogio::time_point instante_anterior = Relogio::now();
	while (interface.esta_aberta()){
		interface.processar_eventos();
		if (!interface.esta_aberta()) {
			break;
		}
		Relogio::time_point instante_atual = Relogio::now();
		Simulacao::Duracao tempo_decorrido = instante_atual - instante_anterior;
		instante_anterior = instante_atual;

		simulacao.tempo_avancar(tempo_decorrido);
		interface.desenhar(simulacao.get_mundo());
	}
}