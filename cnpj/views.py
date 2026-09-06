from django.shortcuts import render, get_object_or_404
from django.db.models import Count
from django.core.paginator import Paginator
from .models import Empresa, Estabelecimento, Socio, Municipio, Cnae


def home(request):
    situacoes = {
        '01': 'Nula', '02': 'Ativa', '03': 'Suspensa',
        '04': 'Inapta', '08': 'Baixada',
    }
    por_situacao = [
        {'label': situacoes.get(item['situacao_cadastral'], item['situacao_cadastral'] or 'Não informado'),
         'total': item['total']}
        for item in (
            Estabelecimento.objects.values('situacao_cadastral')
            .annotate(total=Count('id'))
            .order_by('-total')
        )
    ]

    portes = {'00': 'Não informado', '01': 'Microempresa', '03': 'Empresa de Pequeno Porte', '05': 'Demais'}
    por_porte = [
        {'label': portes.get(item['porte_empresa'], item['porte_empresa'] or 'Não informado'),
         'total': item['total']}
        for item in (
            Empresa.objects.values('porte_empresa')
            .annotate(total=Count('cnpj_basico'))
            .order_by('-total')
        )
    ]

    contexto = {
        'total_empresas': Empresa.objects.count(),
        'total_estabelecimentos': Estabelecimento.objects.count(),
        'total_ativos': Estabelecimento.objects.filter(situacao_cadastral='02').count(),
        'total_socios': Socio.objects.count(),
        'por_uf': (
            Estabelecimento.objects.exclude(uf='')
            .values('uf')
            .annotate(total=Count('id'))
            .order_by('-total')[:10]
        ),
        'por_situacao': por_situacao,
        'por_porte': por_porte,
        'top_cnaes': (
            Estabelecimento.objects.exclude(cnae_principal__isnull=True)
            .values('cnae_principal__descricao')
            .annotate(total=Count('id'))
            .order_by('-total')[:10]
        ),
        'top_naturezas': (
            Empresa.objects.exclude(natureza_juridica__isnull=True)
            .values('natureza_juridica__descricao')
            .annotate(total=Count('cnpj_basico'))
            .order_by('-total')[:10]
        ),
        'top_municipios': (
            Estabelecimento.objects.exclude(municipio__isnull=True)
            .values('municipio__nome', 'uf')
            .annotate(total=Count('id'))
            .order_by('-total')[:10]
        ),
    }
    return render(request, 'cnpj/home.html', contexto)


def buscar(request):
    termo = request.GET.get('q', '').strip()
    resultados = []

    if termo:
        if termo.isdigit():
            resultados = Empresa.objects.filter(cnpj_basico__startswith=termo[:8])[:50]
        else:
            resultados = Empresa.objects.filter(razao_social__icontains=termo)[:50]

    contexto = {'termo': termo, 'resultados': resultados}
    return render(request, 'cnpj/buscar.html', contexto)


def detalhe_empresa(request, cnpj_basico):
    empresa = get_object_or_404(Empresa, cnpj_basico=cnpj_basico)
    estabelecimentos = empresa.estabelecimentos.select_related('municipio', 'cnae_principal').all()
    socios = empresa.socios.select_related('qualificacao_socio').all()

    contexto = {
        'empresa': empresa,
        'estabelecimentos': estabelecimentos,
        'socios': socios,
    }
    return render(request, 'cnpj/detalhe_empresa.html', contexto)


def listar(request):
    estabelecimentos = (
        Estabelecimento.objects
        .select_related('empresa', 'municipio', 'cnae_principal')
        .order_by('id')
    )

    uf = request.GET.get('uf', '')
    municipio_id = request.GET.get('municipio', '')
    situacao = request.GET.get('situacao', '')
    cnae_id = request.GET.get('cnae', '')

    if uf:
        estabelecimentos = estabelecimentos.filter(uf=uf)
    if municipio_id:
        estabelecimentos = estabelecimentos.filter(municipio_id=municipio_id)
    if situacao:
        estabelecimentos = estabelecimentos.filter(situacao_cadastral=situacao)
    if cnae_id:
        estabelecimentos = estabelecimentos.filter(cnae_principal_id=cnae_id)

    paginator = Paginator(estabelecimentos, 25)
    pagina = request.GET.get('page', 1)
    resultados = paginator.get_page(pagina)

    municipios_disponiveis = Municipio.objects.none()
    if uf:
        codigos_municipio = (
            Estabelecimento.objects.filter(uf=uf)
            .exclude(municipio__isnull=True)
            .values_list('municipio_id', flat=True)
            .distinct()
        )
        municipios_disponiveis = Municipio.objects.filter(codigo__in=codigos_municipio).order_by('nome')

    codigos_cnae = (
        Estabelecimento.objects.exclude(cnae_principal__isnull=True)
        .values_list('cnae_principal_id', flat=True)
        .distinct()
    )
    cnaes_disponiveis = Cnae.objects.filter(codigo__in=codigos_cnae).order_by('descricao')

    contexto = {
        'resultados': resultados,
        'ufs': Estabelecimento.objects.exclude(uf='').values_list('uf', flat=True).distinct().order_by('uf'),
        'municipios': municipios_disponiveis,
        'cnaes': cnaes_disponiveis,
        'filtros': {'uf': uf, 'municipio': municipio_id, 'situacao': situacao, 'cnae': cnae_id},
    }
    return render(request, 'cnpj/listar.html', contexto)