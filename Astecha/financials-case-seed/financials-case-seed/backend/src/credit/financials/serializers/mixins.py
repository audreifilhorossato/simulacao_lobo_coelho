"""``UpperCaseKeysMixin`` — espelho do mixin da plataforma Astecha.

Toda tabela exposta pela API responde com as chaves em MAIÚSCULA
(``{"COMPANY_ID": 1, "NAME": "..."}``), porque é assim que a coluna se chama no
Snowflake e é assim que o resto da plataforma consome. A ESCRITA aceita as duas
formas — um payload montado copiando uma resposta tem que funcionar.

Não invente um envelope diferente: o frontend da Astecha já lê neste formato.
"""


class UpperCaseKeysMixin:
    def to_representation(self, instance):
        data = super().to_representation(instance)
        return {str(k).upper(): v for k, v in data.items()}

    def to_internal_value(self, data):
        if isinstance(data, dict):
            data = {str(k).lower(): v for k, v in data.items()}
        return super().to_internal_value(data)
