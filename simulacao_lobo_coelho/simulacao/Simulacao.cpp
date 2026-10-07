#include "simulacao/Simulacao.h"



Simulacao::Simulacao(std::size_t linhas, std::size_t colunas) 
	:mundo(linhas, colunas), 
	tempo_acumulado(0.0), 
	tick_duracao(0.2), 
	tick_numero(0),
	gerador(semente_base), //semente fixa por enquanto
	probabilidade_nascimento_planta(0.001),
	linhas(static_cast<int>(linhas)),
	colunas(static_cast<int>(colunas))
{
	setup_inicial();
}

void Simulacao::tick_atualizar() {

	++tick_numero;
	const std::vector<AnimalId> animais_mortos = matar_animais();

	gerar_carcacas(animais_mortos);

	destruir_carcacas();

	const std::vector<Acao> propostas = processar_animais();

	const std::vector<Acao> aprovadas = resolver_conflitos(propostas);

	executar_acoes(aprovadas);

	gerar_plantas();
}

void Simulacao::setup_inicial(){
	std::uniform_int_distribution<int> chance(7, 14);
	const int n_animais = chance(gerador);

	for (int i = 0; i < n_animais; ++i) {
		std::uniform_int_distribution<int> g_linha(0, linhas - 1);
		std::uniform_int_distribution<int> g_coluna(0, colunas - 1);
		const int linha = g_linha(gerador);
		const int coluna = g_coluna(gerador);

		Especie especie = (i % 2 == 0) ? Especie::Coelho : Especie::Lobo;

		int energia_inicial = (especie == Especie::Coelho) ? ENERGIA_PRIMEIROS_COELHOS : ENERGIA_PRIMEIROS_LOBOS;
		Posicao posicao = {linha, coluna};
		mundo.adicionar_animal(especie, posicao, energia_inicial, tick_numero);
	}
}

void Simulacao::destruir_carcacas() {
	std::vector<AnimalId> carcacas_para_destruir;
	for (const auto& par : mundo.get_carcacas()) {
		const Carcaca& carcaca = par.second;
		if (carcaca.get_idade(tick_numero) >= LIFETIME_CARCACA) {
			carcacas_para_destruir.push_back(carcaca.get_id_original());
		}
		if (carcaca.get_energia_nutricional() <= 0) {
			carcacas_para_destruir.push_back(carcaca.get_id_original());
		}
	}

	for (const AnimalId id : carcacas_para_destruir) {
		mundo.remover_carcaca(id);
	}
}

const Tick Simulacao::get_tick_numero() const{
	return tick_numero;
}

std::vector<Acao> Simulacao::resolver_conflitos(const std::vector<Acao>& acoes) {

	std::map<std::pair<int, int>, std::vector<Acao>> grupos_por_destino;

	for (const auto& acao : acoes) {
		grupos_por_destino[{acao.destino.linha, acao.destino.coluna}].push_back(acao);
	}

	std::vector<std::vector<Acao>> matriz_org_posicao;

	for (const auto& par : grupos_por_destino) {
		const std::vector<Acao>& acoes_no_mesmo_destino = par.second;
		matriz_org_posicao.push_back(acoes_no_mesmo_destino);
		
	}

	std::deque<Acao> acoes_fazer;

	for (int i = 0; i < matriz_org_posicao.size(); i++) {
		std::optional<Acao> prioritaria;
		int maior_energia = -1;
		for (int j = 0; j < matriz_org_posicao[i].size(); j++) {
			
			if (matriz_org_posicao[i][j].tipo == TipoAcao::Matar) {
				acoes_fazer.push_front(matriz_org_posicao[i][j]);
			}

			if (matriz_org_posicao[i][j].tipo == TipoAcao::Esperar) {
				acoes_fazer.push_back(matriz_org_posicao[i][j]);
				break;
			}

			if (matriz_org_posicao[i][j].tipo == TipoAcao::Comer) {
				acoes_fazer.push_back(matriz_org_posicao[i][j]);
				break;
			}

			Animal* animal = mundo.buscar_animal(matriz_org_posicao[i][j].animal_id);
			if (animal == nullptr){
				continue;
			}

			if (animal->get_energia() > maior_energia) {
				prioritaria = matriz_org_posicao[i][j];
				maior_energia = animal->get_energia();
				continue;
			}

			if (animal->get_energia() == maior_energia) {
				maior_energia = -1;
				prioritaria = std::nullopt;
			}
		}
		if (prioritaria == std::nullopt || maior_energia == -1) {
			continue;
		}
		acoes_fazer.push_back(prioritaria.value());
	}

	return std::vector<Acao>(acoes_fazer.begin(), acoes_fazer.end());
}

void Simulacao::executar_acoes(const std::vector<Acao>& acoes){
	for (const Acao& acao : acoes){
		if (acao.tipo == TipoAcao::Matar) {
			Animal* animal_ponteiro = mundo.buscar_animal(acao.animal_id);
			if (animal_ponteiro == nullptr) {
				continue;
			}

			const Celula& celula_alvo = mundo.get_tabuleiro().obter(acao.destino);

			if (!celula_alvo.animalId.has_value()) {
				continue;
			}

			Animal* animal_alvo = mundo.buscar_animal(celula_alvo.animalId.value());

			if (animal_alvo == nullptr) {
				continue;
			}

			animal_alvo->alterar_vivo();
		}

		else if (acao.tipo == TipoAcao::Mover){
			if (!mundo.mover_animal(acao.animal_id, acao.destino)) {
				continue;
			}

			Animal* animal_ponteiro = mundo.buscar_animal(acao.animal_id);

			if (animal_ponteiro == nullptr){
				continue;
			}

			if (animal_ponteiro->get_vivo() == false) {
				continue;
			}

			if (animal_ponteiro->get_especie() == Especie::Coelho){
				if (animal_ponteiro->get_idade(tick_numero) < IDADE_REPRODUCAO_COELHO) {
					continue;
				}
				animal_ponteiro->gastar_energia(CUSTO_MOVIMENTO_COELHO);
			}
			else if (animal_ponteiro->get_especie() == Especie::Lobo){
				if (animal_ponteiro->get_idade(tick_numero) < IDADE_REPRODUCAO_LOBO) {
					continue;
				}
				animal_ponteiro->gastar_energia(CUSTO_MOVIMENTO_LOBO);
			}
		}
		else if (acao.tipo == TipoAcao::Comer){

			Animal* animal_ponteiro = mundo.buscar_animal(acao.animal_id);

			if (animal_ponteiro == nullptr) {
				continue;
			}

			if (animal_ponteiro->get_vivo() == false) {
				continue;
			}

			if (animal_ponteiro->get_especie() == Especie::Coelho) {
				if (!mundo.remover_planta(acao.destino)) {
					continue;
				}
				animal_ponteiro->ganhar_energia(ENERGIA_DA_PLANTA);
			}
			else if (animal_ponteiro->get_especie() == Especie::Lobo) {
				const Celula& celula_alvo = mundo.get_tabuleiro().obter(acao.destino);
				const std::optional<AnimalId> carcaca_id = celula_alvo.carcacaId;

				if (!carcaca_id.has_value()) {
					continue;
				}

				if (!mundo.remover_carcaca(carcaca_id.value())) {
					continue;
				}
				animal_ponteiro->ganhar_energia(ENERGIA_DA_CARCACA);
			}
		}

		else if (acao.tipo == TipoAcao::Reproduzir) {

			Animal* animal_ponteiro = mundo.buscar_animal(acao.animal_id);
			int custo_reproducao = 0;
			if (animal_ponteiro == nullptr) {
				continue;
			}

			if (animal_ponteiro->get_especie() == Especie::Coelho) {
				custo_reproducao = CUSTO_REPRODUZIR_COELHO;
			}
			else if (animal_ponteiro->get_especie() == Especie::Lobo) {
				custo_reproducao = CUSTO_REPRODUZIR_LOBO;
			}

			if (animal_ponteiro->get_energia() < custo_reproducao) {
				continue;
			}

			mundo.adicionar_animal(
				animal_ponteiro->get_especie(),
				acao.destino,
				(animal_ponteiro->get_energia())/2,
				tick_numero
			);

			animal_ponteiro->gastar_energia(custo_reproducao);

		}
	}
}

std::vector<AnimalId> Simulacao::matar_animais() {
	std::vector<AnimalId> animais_mortos;
	Tick idade_max = 200;

	for (const auto& [id, animal] : mundo.get_animais()) {

		Especie especie = animal.get_especie();

		if (especie == Especie::Coelho){
			idade_max = IDADE_MAX_COELHO;
		}
		else if (especie == Especie::Lobo){
			idade_max = IDADE_MAX_LOBO;
		}

		Tick idade = animal.get_idade(tick_numero);
		int energia = animal.get_energia();

		if (animal.get_vivo() == false) {
			animais_mortos.push_back(id);
			continue;
		}

		if (idade > idade_max) {
			animais_mortos.push_back(id);
			continue;
		}
	
		if (energia <= 0) {
			animais_mortos.push_back(id);
			continue;
		}
	}

	return animais_mortos;
}

void Simulacao::gerar_carcacas(const std::vector<AnimalId>& animais_mortos) {
	for (AnimalId id : animais_mortos) {
		Animal* animal = mundo.buscar_animal(id);

		if (animal == nullptr) {
			continue;
		}	

		mundo.adicionar_carcaca(*animal, tick_numero);

		mundo.remover_animal(id);
	}	
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

std::vector<Acao> Simulacao::processar_animais() {

	std::vector<Acao> acoes;

	for (const auto& [id, animal] : mundo.get_animais()) {

		Animal* animal_ponteiro = mundo.buscar_animal(animal.get_id());

		if (animal_ponteiro == nullptr){
			continue;
		}

		if (animal.get_vivo() == false) {
			continue;
		}

		int raio_visao = 0; ///< Raio 0 como padrão
		if (animal_ponteiro->get_especie() == Especie::Coelho) {
			animal_ponteiro->gastar_energia(CUSTO_POR_TICK_COELHO);
			raio_visao = RAIO_VISAO_COELHO;
			
		}
		else if (animal_ponteiro->get_especie() == Especie::Lobo) {
			animal_ponteiro->gastar_energia(CUSTO_POR_TICK_LOBO);
			raio_visao = RAIO_VISAO_LOBO;
		}

		const VisaoAnimal visao = mundo.observar(animal.get_posicao(), raio_visao);

		const Acao acao = sistema_decisao.decidir(animal, visao, gerador,tick_numero);

		acoes.push_back(acao);
	}

	return acoes;
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

std::vector<Acao> Simulacao::processar_animais_paralelo() {

	std::vector<Animal*> vivos;
	vivos.reserve(mundo.get_animais().size());
	for (const auto& [id, animal] : mundo.get_animais()) {
		Animal* a = mundo.buscar_animal(id);
		if (a != nullptr && a->get_vivo()) {
			vivos.push_back(a);
		}
	}

	for (Animal* a : vivos) {
		if (a->get_especie() == Especie::Coelho)      a->gastar_energia(CUSTO_POR_TICK_COELHO);
		else if (a->get_especie() == Especie::Lobo)   a->gastar_energia(CUSTO_POR_TICK_LOBO);
	}

	std::vector<Acao> acoes(vivos.size());  

	paralelo_para(vivos.size(), [&](std::size_t i) {
		const Animal& aminal = *vivos[i];

		int raio_visao = 0;
		if (aminal.get_especie() == Especie::Coelho)      raio_visao = RAIO_VISAO_COELHO;
		else if (aminal.get_especie() == Especie::Lobo)   raio_visao = RAIO_VISAO_LOBO;

		const VisaoAnimal visao = mundo.observar(aminal.get_posicao(), raio_visao);

		std::mt19937 gerador_local = gerador_paralelo(semente_base, tick_numero, aminal.get_id());
		acoes[i] = sistema_decisao.decidir(aminal, visao, gerador_local, tick_numero);
		});

	return acoes;
}

std::mt19937 Simulacao::gerador_paralelo(std::uint64_t semente, int tick, int id) {
	std::seed_seq seq{ static_cast<std::uint32_t>(semente),
					   static_cast<std::uint32_t>(semente >> 32),
					   static_cast<std::uint32_t>(tick),
					   static_cast<std::uint32_t>(id) };
	return std::mt19937(seq);
}

