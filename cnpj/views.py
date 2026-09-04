from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Count
from django.core.paginator import Paginator
from .models import Empresa, Estabelecimento, Municipio, Cnae


def home(request):
    contexto = {
        'total_empresas': Empresa.objects.count(),
        'total_estabelecimentos': Estabelecimento.objects.count(),
        'total_ativos': Estabelecimento.objects.filter(situacao_cadastral='02').count(),
        'por_uf': (
            Estabelecimento.objects.exclude(uf='')
            .values('uf')
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
            # busca por CNPJ (basico ou completo, so digitos)
            resultados = Empresa.objects.filter(cnpj_basico__startswith=termo[:8])[:50]
        else:
            # busca por razao social (case-insensitive, contem o termo)
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
    estabelecimentos = Estabelecimento.objects.select_related('empresa', 'municipio', 'cnae_principal').all()

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

    contexto = {
        'resultados': resultados,
        'ufs': Estabelecimento.objects.exclude(uf='').values_list('uf', flat=True).distinct().order_by('uf'),
        'filtros': {'uf': uf, 'municipio': municipio_id, 'situacao': situacao, 'cnae': cnae_id},
    }
    return render(request, 'cnpj/listar.html', contexto)