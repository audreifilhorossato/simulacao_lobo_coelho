#include "dominio/Animal.h"

Animal::Animal(
	AnimalId id,
	Especie especie,
	Posicao posicao,
	int energia_inicial,
	Tick tick_nascimento
):
	id(id),
	especie(especie),
	posicao(posicao),
	energia(energia_inicial),
	tick_nascimento(tick_nascimento),
	tempo_reproducao(0),
	vivo(true)
{
};

void Animal::alterar_vivo() {
	vivo = false;
}

// Retorna 0 para evitar idade negativa caso o tick atual seja anterior ao nascimento
Tick Animal::get_idade(Tick tick_atual) const {
	if (tick_atual <= tick_nascimento) {
		return 0;
	}
	return tick_atual - tick_nascimento;
	
}


void Animal::gastar_energia(int gasto) {
	energia -= gasto;
}

void Animal::ganhar_energia(int ganho) {
	energia += ganho;
	if (energia > ENERGIA_MAX_COELHO) {
		energia = ENERGIA_MAX_COELHO;
	}
}

bool Animal::esta_sem_energia() const{
	return energia <= 0;
}


void Animal::definir_posicao(Posicao nova_posicao) {
	posicao = nova_posicao;
}

// --- Getters simples: apenas retornam o valor do atributo correspondente,
// sem lógica adicional. Documentação completa de cada um está no Animal.h. ---

AnimalId Animal::get_id() const {
	return id;
}

Tick Animal::get_nascimento() const {
	return tick_nascimento;
}

Especie Animal::get_especie() const {
	return especie;
}

Posicao Animal::get_posicao() const {
	return posicao;
}

int Animal::get_energia() const{
	return energia;
}

int Animal::get_tempo_reproducao() const {
	return tempo_reproducao;
}

bool Animal::get_vivo() const {
	return vivo;
}

Carcaca::Carcaca(const Animal& animal_morto, Tick tick_numero)
	: id_original(animal_morto.get_id()),
	especie(animal_morto.get_especie()),
	posicao(animal_morto.get_posicao()),
	energia_nutricional(animal_morto.get_energia()),
	tick_nascimento(tick_numero)
{
}

AnimalId Carcaca::get_id_original() const {
	return id_original;
}

Especie Carcaca::get_especie() const {
	return especie;
}

Posicao Carcaca::get_posicao() const {
	return posicao;
}

int Carcaca::get_energia_nutricional() const {
	return energia_nutricional;
}

Tick Carcaca::get_idade(Tick tick_atual) const {
	if (tick_atual <= tick_nascimento) {
		return 0;
	}
	return tick_atual - tick_nascimento;
}