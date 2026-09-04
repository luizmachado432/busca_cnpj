from django.db import models

class Cnae(models.Model):
    codigo = models.CharField(max_length=7, primary_key=True)
    descricao = models.CharField(max_length=200)

class Municipio(models.Model):
    codigo = models.CharField(max_length=4, primary_key=True)
    nome = models.CharField(max_length=100)

class NaturezaJuridica(models.Model):
    codigo = models.CharField(max_length=4, primary_key=True)
    descricao = models.CharField(max_length=200)

class Motivo(models.Model):
    codigo = models.CharField(max_length=2, primary_key=True)
    descricao = models.CharField(max_length=200)

class Qualificacao(models.Model):
    codigo = models.CharField(max_length=2, primary_key=True)
    descricao = models.CharField(max_length=200)
class Empresa(models.Model):
    cnpj_basico = models.CharField(max_length=8, primary_key=True)
    razao_social = models.CharField(max_length=200)
    natureza_juridica = models.ForeignKey(NaturezaJuridica, on_delete=models.SET_NULL, null=True)
    qualificacao_responsavel = models.ForeignKey(Qualificacao, on_delete=models.SET_NULL, null=True)
    capital_social = models.DecimalField(max_digits=15, decimal_places=2)
    porte_empresa = models.CharField(max_length=2, blank=True)
    ente_federativo_responsavel = models.CharField(max_length=100, blank=True)
class Socio(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='socios')
    identificador_socio = models.CharField(max_length=1)
    nome_socio = models.CharField(max_length=200)
    cpf_cnpj_socio = models.CharField(max_length=14, blank=True)
    qualificacao_socio = models.ForeignKey(Qualificacao, on_delete=models.SET_NULL, null=True, related_name='+')
    data_entrada_sociedade = models.DateField(null=True)
    pais = models.CharField(max_length=3, blank=True)
    representante_legal = models.CharField(max_length=14, blank=True)
    nome_representante = models.CharField(max_length=200, blank=True)
    qualificacao_representante = models.ForeignKey(Qualificacao, on_delete=models.SET_NULL, null=True, related_name='+', blank=True)
    faixa_etaria = models.CharField(max_length=1, blank=True)

class Estabelecimento(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='estabelecimentos')
    cnpj_ordem = models.CharField(max_length=4)
    cnpj_dv = models.CharField(max_length=2)
    identificador_matriz_filial = models.CharField(max_length=1)
    nome_fantasia = models.CharField(max_length=200, blank=True)
    situacao_cadastral = models.CharField(max_length=2)
    data_situacao_cadastral = models.DateField(null=True)
    motivo_situacao_cadastral = models.ForeignKey(Motivo, on_delete=models.SET_NULL, null=True)
    data_inicio_atividade = models.DateField(null=True)
    cnae_principal = models.ForeignKey(Cnae, on_delete=models.SET_NULL, null=True, related_name='+')
    cnae_secundaria = models.CharField(max_length=1000, blank=True)  # lista crua; pode virar M2M depois se quiser
    tipo_logradouro = models.CharField(max_length=30, blank=True)
    logradouro = models.CharField(max_length=200, blank=True)
    numero = models.CharField(max_length=20, blank=True)
    complemento = models.CharField(max_length=200, blank=True)
    bairro = models.CharField(max_length=100, blank=True)
    cep = models.CharField(max_length=8, blank=True)
    uf = models.CharField(max_length=2, blank=True)
    municipio = models.ForeignKey(Municipio, on_delete=models.SET_NULL, null=True)
    email = models.CharField(max_length=200, blank=True)

    @property
    def cnpj_completo(self):
        return f"{self.empresa.cnpj_basico}{self.cnpj_ordem}{self.cnpj_dv}"