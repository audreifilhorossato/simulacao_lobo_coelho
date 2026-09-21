#include "simulacao/Simulacao.h"

namespace{
	constexpr int CUSTO_MOVIMENTO_COELHO = 1;
	constexpr int CUSTO_POR_TICK_COELHO = 1;
	constexpr int IDADE_MAX_COELHO = 200;
	constexpr int ENERGIA_DA_PLANTA = 30;
	constexpr int RAIO_VISAO_COELHO = 4;
}

Simulacao::Simulacao(std::size_t linhas, std::size_t colunas) 
	:mundo(linhas, colunas), 
	tempo_acumulado(0.0), 
	tick_duracao(0.), 
	tick_numero(0),
	gerador(1), //semente fixa por enquanto
	probabilidade_nascimento_planta(0.001) 
{
	mundo.adicionar_animal(
		Especie::Coelho,
		{ 2, 3 },
		100,
		tick_numero
	);

	mundo.adicionar_animal(
		Especie::Coelho,
		{ 7, 8 },
		100,
		tick_numero
	);

	mundo.adicionar_animal(
		Especie::Coelho,
		{ 11, 15 },
		100,
		tick_numero
	);

	mundo.adicionar_animal(
		Especie::Coelho,
		{ 20, 3 },
		100,
		tick_numero
	);

	mundo.adicionar_animal(
		Especie::Coelho,
		{ 24, 6 },
		100,
		tick_numero
	);

}

void Simulacao::tick_atualizar() {

	++tick_numero;
	matar_animais();

	const std::vector<Acao> propostas = processar_animais();

	const std::vector<Acao> aprovadas = resolver_conflitos(propostas);

	executar_acoes(aprovadas);

	gerar_plantas();
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

	std::vector<Acao> acoes_fazer;

	for (int i = 0; i < matriz_org_posicao.size(); i++) {
		std::optional<Acao> prioritaria;
		int maior_energia = -1;
		for (int j = 0; j < matriz_org_posicao[i].size(); j++) {
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

	return acoes_fazer;
}

void Simulacao::executar_acoes(const std::vector<Acao>& acoes){
	for (const Acao& acao : acoes){
		if (acao.tipo == TipoAcao::Mover){
			if (!mundo.mover_animal(acao.animal_id, acao.destino)) {
				continue;
			}

			Animal* animal_ponteiro = mundo.buscar_animal(acao.animal_id);

			if (animal_ponteiro == nullptr){
				continue;
			}

			if (animal_ponteiro->get_especie() == Especie::Coelho){
				animal_ponteiro->gastar_energia(CUSTO_MOVIMENTO_COELHO);
			}
		}
		if (acao.tipo == TipoAcao::Comer){
			if (!mundo.remover_planta(acao.destino)) {
				continue;
			}

			Animal* animal_ponteiro = mundo.buscar_animal(acao.animal_id);

			if (animal_ponteiro == nullptr) {
				continue;
			}

			if (animal_ponteiro->get_especie() == Especie::Coelho) {
				animal_ponteiro->ganhar_energia(ENERGIA_DA_PLANTA);
			}
		}
	}
}

void Simulacao::matar_animais() {
	std::vector<AnimalId> animais_mortos;
	const Tick idade_max = IDADE_MAX_COELHO;
	for (const auto& [id, animal] : mundo.get_animais()) {

		Tick idade = animal.get_idade(tick_numero);
		int energia = animal.get_energia();

		if (energia <= 0 || idade > idade_max) {
			animais_mortos.push_back(id);
		}

	}

	for (AnimalId id : animais_mortos) {
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

		int raio_visao = 0; ///< Raio 0 como padrão
		if (animal_ponteiro->get_especie() == Especie::Coelho) {
			animal_ponteiro->gastar_energia(CUSTO_POR_TICK_COELHO);
			raio_visao = RAIO_VISAO_COELHO;
			
		}

		const VisaoAnimal visao = mundo.observar(animal.get_posicao(), raio_visao);

		const Acao acao = sistema_decisao.decidir(animal, visao, gerador);

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

