#include "dominio/Mundo.h"

Mundo::Mundo(std::size_t linhas, std::size_t colunas) 
	:tabuleiro(linhas, colunas),
	animais(),
	proximo_id(1)
{}

void Mundo::remover_animal(AnimalId id) {
	std::unordered_map<AnimalId, Animal>::iterator animal_encontrado = animais.find(id);
	if (animal_encontrado == animais.end()){
		return;
	}

	const Posicao posicao = animal_encontrado->second.get_posicao();

	if (tabuleiro.posicao_valida(posicao)){
		Celula& celula = tabuleiro.obter(posicao);

		if (celula.animalId.has_value() && celula.animalId.value() == id){
			celula.animalId.reset();
		}
	}
	animais.erase(animal_encontrado);
}

VisaoAnimal Mundo::observar(Posicao centro, int raio) const {
	VisaoAnimal visao;
	if (raio < 0){
		raio = 0;
	}

	if (tabuleiro.get_linhas() == 0 || tabuleiro.get_colunas() == 0){
		return visao;
	}

	
	centro = tabuleiro.normatizar_posicao(centro);
	visao.centro = centro;
	visao.celula_central = tabuleiro.obter({ centro.linha, centro.coluna });

	for (int i = centro.linha - raio; i <= centro.linha + raio ; i++){
		for (int j = centro.coluna - raio; j <= centro.coluna + raio; j++) {
			const int dist_linha = i - centro.linha; 
			const int dist_coluna = j - centro.coluna;
			if ((dist_linha * dist_linha) + (dist_coluna * dist_coluna) <= (raio * raio)) {
				CelulaObservada observada;
				observada.existe = true;

				observada.posicao_relativa = {dist_linha,dist_coluna};
				observada.posicao = tabuleiro.normatizar_posicao({ i,j });

				const Celula& celula = tabuleiro.obter(observada.posicao); 
				observada.tem_planta = celula.tem_planta; 
				observada.animal_id = celula.animalId;

				if (celula.animalId.has_value()) { 
					const Animal* animal_encontrado = buscar_animal(celula.animalId.value()); 
					if (animal_encontrado != nullptr) { 
						observada.especie_animal = animal_encontrado->get_especie(); 
					} 
				}
				visao.celulas.push_back(observada);
			}
		}
	}
	return visao;
}

std::optional<AnimalId> Mundo::adicionar_animal(Especie especie, Posicao posicao, int energia_inicial, Tick tick_atual) {
	
	const Posicao posicao_norm = tabuleiro.normatizar_posicao(posicao);

	Celula& celula = tabuleiro.obter(posicao_norm);

	if (celula.animalId.has_value()) {
		return std::nullopt;
	}

	const AnimalId novo_id = proximo_id;

	Animal novo_animal(
		novo_id,
		especie,
		posicao_norm,
		energia_inicial,
		tick_atual
	);

	animais.emplace(novo_id, novo_animal);

	celula.animalId = novo_id;
	proximo_id++;

	return novo_id;
}

const Animal* Mundo::buscar_animal(AnimalId id) const{
	std::unordered_map<AnimalId, Animal>::const_iterator animal_encontrado = animais.find(id);

	if (animal_encontrado == animais.end()) {
		return nullptr;
	}

	return &animal_encontrado->second;
}

Animal* Mundo::buscar_animal(AnimalId id){
	std::unordered_map<AnimalId, Animal>::iterator animal_encontrado = animais.find(id);

	if (animal_encontrado == animais.end()) {
		return nullptr;
	}

	return &animal_encontrado->second;
}

const std::unordered_map<AnimalId, Animal>& Mundo::get_animais() const{
	return animais;
}

const Tabuleiro& Mundo::get_tabuleiro() const{
	return tabuleiro;
}

bool Mundo::mover_animal(AnimalId id, Posicao destino) {
	std::unordered_map<AnimalId, Animal>::iterator encontrado = animais.find(id);

	if (encontrado == animais.end()) {
		return false;
	}

	destino = tabuleiro.normatizar_posicao(destino);

	Animal& animal = encontrado->second;

	const Posicao origem = animal.get_posicao();

	if (!tabuleiro.posicao_valida(origem)) {
		return false;
	}

	if (origem.linha == destino.linha && origem.coluna == destino.coluna){
		return false;
	}

	Celula& celula_origem =
		tabuleiro.obter(origem);

	Celula& celula_destino =
		tabuleiro.obter(destino);

	if (!celula_origem.animalId.has_value() || celula_origem.animalId.value() != id){
		return false;
	}

	if (celula_destino.animalId.has_value()){
		return false;
	}

	celula_origem.animalId.reset();
	celula_destino.animalId = id;

	animal.definir_posicao(destino);

	return true;

}

bool Mundo::adicionar_planta(Posicao posicao) {
	const Posicao posicao_norm = tabuleiro.normatizar_posicao(posicao);
	
	Celula& celula = tabuleiro.obter(posicao_norm);
	if (celula.tem_planta) {
		return false;
	}
	celula.tem_planta = true;
	return true;
}

bool Mundo::remover_planta(Posicao posicao) {
	const Posicao posicao_norm = tabuleiro.normatizar_posicao(posicao);

	Celula& celula = tabuleiro.obter(posicao_norm);
	if (!celula.tem_planta) {
		return false;
	}
	celula.tem_planta = false;
	return true;
}