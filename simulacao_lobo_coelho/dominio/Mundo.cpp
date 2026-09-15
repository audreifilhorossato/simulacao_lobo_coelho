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

std::optional<AnimalId> Mundo::adicionar_animal(Especie especie, Posicao posicao, int energia_inicial, Tick tick_atual) {
	if (!tabuleiro.posicao_valida(posicao)) {
		return std::nullopt;
	}

	Celula& celula = tabuleiro.obter(posicao);

	if (celula.animalId.has_value()) {
		return std::nullopt;
	}

	const AnimalId novo_id = proximo_id;

	Animal novo_animal(
		novo_id,
		especie,
		posicao,
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

bool Mundo::adicionar_planta(Posicao posicao) {
	Celula& celula = tabuleiro.obter(posicao);
	if (celula.tem_planta) {
		return false;
	}
	celula.tem_planta = true;
	return true;
}