#include "dominio/Animal.h"

Animal::Animal(
	AnimalId id,
	Especie especie,
	Posicao posicao,
	Tick tick_nascimento,
	int energia_inicial
):
	id(id),
	especie(especie),
	posicao(posicao),
	energia(energia_inicial),
	idade(tick_nascimento),
	tempo_reproducao(0),
	vivo(true)
{
};

void Animal::alterar_vivo() {
	vivo = !vivo;
}

Tick Animal::get_idade(Tick tick_atual) const {
	if (tick_atual <= tick_nascimento) {
		return 0;
	}
	else
	{
		return tick_atual - tick_nascimento;
	}
}


void Animal::gastar_energia(int gasto) {
	energia -= gasto;
}

void Animal::ganhar_energia(int ganho) {
	energia += ganho;
}

bool Animal::esta_sem_energia() const{
	if (energia <= 0) {
		return true;
	}
	else
	{
		return false;
	}
}

void Animal::definir_posicao(Posicao nova_posicao) {
	posicao = nova_posicao;
}

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

