"""Atualiza as informações do concurso (SEFAZ/AL 2026 - Cebraspe) nas páginas internas. Idempotente."""
import re

PUB = '/app/frontend/public'
PAGES = ['inscricao', 'dados-inscricao', 'confirmacao', 'inscricao-realizada', 'pagamento-pix', 'minhas-inscricoes']

REPL = [
    ('Vestibular Unesp 2027 | Fundação VUNESP', 'SEFAZ/AL 2026 | Cebraspe'),
    ('<h3 class="vn-keep">Vestibular Unesp 2027</h3><p class="vn-sub">Universidade Estadual Paulista - UNESP</p>',
     '<h3 class="vn-keep">SEFAZ/AL 2026</h3><p class="vn-sub">Secretaria de Estado da Fazenda de Alagoas</p>'),
    ('<h3>Vestibular Unesp 2027</h3><p class="vn-sub">Universidade Estadual Paulista - UNESP</p>',
     '<h3>SEFAZ/AL 2026</h3><p class="vn-sub">Secretaria de Estado da Fazenda de Alagoas</p>'),
    ('<b>04/09/2026</b>', '<b>17/09/2026</b>'),
    ('<b>20/10/2026</b>', '<b>21/10/2026</b>'),
    ('A Fundação VUNESP atende', 'O Cebraspe atende'),
    ('para fins deste vestibular', 'para fins deste concurso público'),
    ('>Vestibular Unesp 2027 - VNSP2514</option>', '>SEFAZ/AL 2026 - Edital nº 1</option>'),
    ("'Vestibular Unesp 2027 - Fundação VUNESP'", "'SEFAZ/AL 2026 - Cebraspe'"),
    ("'VNSP2514'", "'SEFAZ_AL_26'"),
    ('© FUNDAÇÃO VUNESP — VESTIBULAR UNESP 2027', '© CEBRASPE — SEFAZ/AL 2026'),
    ('alt="Fundação VUNESP"', 'alt="Cebraspe"'),
    ('<img src="/vunesp/vunesp-logo.png"', '<img src="/cebraspe-logo.webp"'),
    ('Fundação VUNESP — Vestibulares e Concursos',
     'Cebraspe — Centro Brasileiro de Pesquisa em Avaliação e Seleção e de Promoção de Eventos'),
    ('margin-top:4px;">Vestibular Unesp 2027</div>', 'margin-top:4px;">SEFAZ/AL 2026</div>'),
    ('Universidade Estadual Paulista (Unesp) - VNSP2514', 'Secretaria de Estado da Fazenda de Alagoas - Edital nº 1'),
    ('atendimento@vunesp.com.br', 'sac@cebraspe.org.br'),
]

for p in PAGES:
    f = f'{PUB}/{p}.html'
    s = open(f, encoding='utf-8').read()
    for a, b in REPL:
        s = s.replace(a, b)
    s = re.sub(r'seduc-theme\.js\?v=\d+', 'seduc-theme.js?v=18', s)
    s = re.sub(r'vunesp/pages\.css\?v=\d+', 'vunesp/pages.css?v=9', s)
    open(f, 'w', encoding='utf-8').write(s)
    left = re.findall(r'(?i)[^<>]{0,30}(?:vunesp|unesp|vestibular)[^<>]{0,30}', re.sub(r'data:[^"\')\s]{100,}', '', s))
    print(p, 'restante:', [x.strip()[:70] for x in left][:8])
