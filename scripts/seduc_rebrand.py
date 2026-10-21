import re, shutil, os, sys

PUB = '/app/frontend/public'
BK = '/app/backup/flow_sesa_ap'
PAGES = ["inscricao.html", "dados-inscricao.html", "confirmacao.html", "pagamento-pix.html",
         "inscricao-realizada.html", "minhas-inscricoes.html"]

CARD = ('<div class="aocp-edital-card" data-testid="edital-card">'
        '<div class="aec-head"><h3>SECRETARIA DA EDUCAÇÃO DO ESTADO DO CEARÁ - SEDUC/CE</h3></div>'
        '<div class="aec-body"><img src="/seduc/cev-logo.png" alt="CEV/UECE" class=rounded-box>'
        '<div class="aec-txt"><strong>Edital Nº 014/2026-SEDUC/SEPLAG</strong><br>Concurso Público de Provas e Títulos '
        'para Provimento de Cargos Efetivos de Professor com Lotação em Estabelecimentos de Ensino da Rede Estadual do Ceará, '
        'vinculados à Secretaria da Educação do Estado do Ceará (SEDUC).</div></div></div>')

FOOTER = ('<footer id="aocp-footer" class="seduc-footer" data-testid="site-footer"><div class="sf-in">'
          '<div class="sf-site"><h2>cev.uece.br</h2><img src="/seduc/emec.png" alt="e-MEC"></div>'
          '<div class="sf-box"><h2>Universidade Estadual do Ceará - UECE</h2><p>Av. Dr. Silas Munguba, 1700 - Campus do Itaperi<br>'
          'Fortaleza, CE<br>(85) 3101-9711<br>CEP: 60.714.903</p></div>'
          '<div class="sf-box"><h2>Comissão Executiva do Vestibular</h2><p>Concurso Professor Seduc 2026<br>Edital Nº 014/2026-SEDUC/SEPLAG</p></div>'
          '</div><div class="sf-copy">© 2026 – Universidade Estadual do Ceará<br>todos os direitos reservados</div></footer>')

COLORS = {
    '#002d4d': '#006b2d', '#1858bf': '#008d3c', '#01bfbf': '#00a84a', '#36a980': '#008d3c', '#2f8f6c': '#006b2d',
    '#0f4cad': '#006b2d', '#1c3053': '#1f3d2b', '#1e3a8a': '#006b2d', '#0d5aa7': '#008d3c', '#174d87': '#006b2d',
    '#17345c': '#1f3d2b', '#2b8a68': '#006b2d', '#0b3a81': '#006b2d', '#2a4270': '#2c4a37', '#001a2c': '#0e2a1a',
    '#2e78ed': '#00a84a', '#337ab7': '#008d3c', '#02142c': '#0e2a1a', '#1e2a3a': '#1f2d24', '#2b3a4d': '#2c3d31',
    '#93a1bb': '#93b39f', '#eef2f7': '#eef6f0', '#f4f7fb': '#f4faf6', '#e6eaf1': '#e6f0e9', '#d5dbe6': '#d5e3da',
}
RGBA = {'rgba(0,45,77': 'rgba(0,107,45', 'rgba(0, 45, 77': 'rgba(0, 107, 45', 'rgba(30,58,138': 'rgba(0,107,45',
        'rgba(24,88,191': 'rgba(0,141,60', 'rgba(54,169,128': 'rgba(0,141,60'}

TEXT = [
    ('Concurso Público da Secretaria de Estado da Administração do Estado do Amapá - Edital 001/2026', 'Concurso Público para Professor da Secretaria da Educação do Estado do Ceará (SEDUC/CE) - Edital 014/2026'),
    ('Concurso Público da Secretaria de Administração do Estado da Bahia (SAEB_BA_26) - Edital 002/2026', 'Concurso Público para Professor da Secretaria da Educação do Estado do Ceará (SEDUC/CE) - Edital 014/2026'),
    ("'002/2026-SAEB-BA'", "'014/2026-SEDUC/SEPLAG'"),
    ('Concurso Público da Secretaria de Estado da Administração do Estado do Amapá', 'Concurso Público para Professor da Secretaria da Educação do Estado do Ceará'),
    ('Secretaria de Estado da Administração do Estado do Amapá', 'Secretaria da Educação do Estado do Ceará (SEDUC/CE)'),
    ('CONCURSO PÚBLICO SAEB-BA', 'CONCURSO PROFESSOR SEDUC 2026'),
    ('Concurso Público SESA/AP - Nº 001/2026', 'Concurso Público SEDUC/CE - Edital Nº 014/2026'),
    ('Instituto AOCP', 'CEV/UECE'),
    ('INSTITUTO AOCP', 'CEV/UECE'),
    ('Concurso Público SAEB_BA_26', 'Concurso Professor Seduc 2026'),
    ('Concurso Público SAEB-BA', 'Concurso Professor Seduc 2026'),
    ('CONCURSO PÚBLICO SAEB_BA_26', 'CONCURSO PROFESSOR SEDUC 2026'),
]


def fix_colors(s):
    def rep(m):
        return COLORS.get(m.group(0).lower(), m.group(0))
    s = re.sub(r'#[0-9a-fA-F]{6}\b', rep, s)
    for a, b in RGBA.items():
        s = s.replace(a, b)
    return s


TITLES = {'inscricao.html': 'Formulário de Inscrição', 'dados-inscricao.html': 'Dados da Inscrição', 'confirmacao.html': 'Confirmação dos Dados', 'pagamento-pix.html': 'Pagamento da Inscrição', 'inscricao-realizada.html': 'Inscrição Realizada', 'minhas-inscricoes.html': 'Minhas inscrições'}
TITLE = ''


def transform(s):
    s = s.replace('<script src="/aocp-header.v3.js"></script>',
                  '<link rel="stylesheet" href="/seduc/seduc-theme.css"><script src="/seduc/seduc-theme.js"></script>')
    s = re.sub(r'<div class="aocp-edital-card" data-testid="edital-card">.*?</div>\s*</div>\s*</div>', CARD, s, count=1, flags=re.S)
    s = re.sub(r'<footer id="aocp-footer">.*?</footer>', FOOTER, s, count=1, flags=re.S)
    s = re.sub(r'<!--\s*Page saved with SingleFile.*?-->', '', s, count=1, flags=re.S)
    s = re.sub(r'(Inscrições de\s*<b>)30/07/2026(</b>\s*a\s*<b>)31/08/2026', r'\g<1>15/09/2026\g<2>15/10/2026', s)
    for a, b in TEXT:
        s = s.replace(a, b)
    s = re.sub(r'<title>[^<]*</title>', '<title>' + TITLE + ' - Concurso Professor Seduc 2026 | CEV/UECE</title>', s, count=1)
    s = re.sub(r'<div class="edhead"><h3>.*?</h3></div>\s*<div class="edbody"><img src="[^"]*" alt="[^"]*">\s*<div class="edtxt">.*?</div>',
               '<div class="edhead"><h3>SECRETARIA DA EDUCAÇÃO DO ESTADO DO CEARÁ - SEDUC/CE</h3></div><div class="edbody"><img src="/seduc/cev-logo.png" alt="CEV/UECE" style="width:200px;border-radius:0"><div class="edtxt"><strong>Edital Nº 014/2026-SEDUC/SEPLAG</strong><br>Concurso Público de Provas e Títulos para Provimento de Cargos Efetivos de Professor com Lotação em Estabelecimentos de Ensino da Rede Estadual do Ceará, vinculados à Secretaria da Educação do Estado do Ceará (SEDUC).</div>', s, count=1, flags=re.S)
    s = s.replace('.edhead{background:linear-gradient(90deg,#f3f8ff,#fff);border-bottom:1px solid #eef2f7;padding:18px 24px}', '.edhead{background:#008d3c;padding:14px 24px}.edhead h3{color:#fff!important;font-family:"OpenSans-Semibold",Helvetica,Arial,sans-serif}')
    if 'seduc-footer' not in s:
        s = s.replace('</body>', FOOTER + '</body>', 1)
    return fix_colors(s)


if __name__ == '__main__':
    os.makedirs(BK, exist_ok=True)
    for p in PAGES:
        src = os.path.join(BK, p)
        if not os.path.exists(src):
            shutil.copy(os.path.join(PUB, p), src)
        s = open(src, encoding='utf-8').read()
        TITLE = TITLES[p]
        out = transform(s)
        open(os.path.join(PUB, p), 'w', encoding='utf-8').write(out)
        print(p, 'card' if 'SEDUC/CE - SEDUC' not in out and 'SEDUC/CE</h3>' in out else 'NO CARD',
              'footer' if 'seduc-footer' in out else 'NO FOOTER', 'hdr' if 'seduc-theme.js' in out else 'NO HDR')
