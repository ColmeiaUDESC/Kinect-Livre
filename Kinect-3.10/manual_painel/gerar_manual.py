"""Gera o manual ilustrado do painel; as imagens são capturas reais do Tk."""
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Image, Table,
                               TableStyle, PageBreak, KeepTogether)
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
OUT=ROOT/'Manual Caixa de Areia - Painel Python.pdf'
for name,file in [('Lato','Lato-Regular.ttf'),('LatoBold','Lato-Bold.ttf'),('LatoItalic','Lato-Italic.ttf')]:
    pdfmetrics.registerFont(TTFont(name,'/usr/share/fonts/truetype/lato/'+file))
pdfmetrics.registerFontFamily('Lato',normal='Lato',bold='LatoBold',italic='LatoItalic',boldItalic='LatoBold')
NAVY=colors.HexColor('#17323F');TEAL=colors.HexColor('#087F82');INK=colors.HexColor('#243B46')
MUTED=colors.HexColor('#526570');PALE=colors.HexColor('#EDF6F5');LINE=colors.HexColor('#D9E3E6')
WIDTH=A4[0]-88
S={
 'title':ParagraphStyle('title',fontName='LatoBold',fontSize=23,leading=27,textColor=NAVY,spaceAfter=12),
 'subtitle':ParagraphStyle('subtitle',fontName='LatoBold',fontSize=13,leading=17,textColor=TEAL,spaceBefore=10,spaceAfter=6),
 'body':ParagraphStyle('body',fontName='Lato',fontSize=10.6,leading=14.5,textColor=INK,spaceAfter=8),
 'small':ParagraphStyle('small',fontName='Lato',fontSize=9,leading=12,textColor=MUTED,spaceAfter=6),
 'caption':ParagraphStyle('caption',fontName='LatoItalic',fontSize=8.5,leading=11,textColor=MUTED,spaceBefore=5,spaceAfter=10),
 'kicker':ParagraphStyle('kicker',fontName='LatoBold',fontSize=9,leading=12,textColor=TEAL,spaceAfter=7),
 'cell':ParagraphStyle('cell',fontName='Lato',fontSize=9.5,leading=12.5,textColor=INK),
 'headcell':ParagraphStyle('headcell',fontName='LatoBold',fontSize=9.5,leading=12.5,textColor=colors.white),
 'cover':ParagraphStyle('cover',fontName='LatoBold',fontSize=37,leading=40,textColor=NAVY,spaceAfter=12),
 'cover_sub':ParagraphStyle('cover_sub',fontName='Lato',fontSize=20,leading=25,textColor=TEAL,spaceAfter=14),
}
items=[]
def p(text,style='body'):return Paragraph(text,S[style])
def text(value,style='body'):items.append(p(value,style))
def space(h=7):items.append(Spacer(1,h))
def title(n,value):
 if items:items.append(PageBreak())
 text(f'GUIA DE USO  /  {n:02d}','kicker')
 h=p(value,'title');h._bookmark=f'sec{n}';items.append(h)
def step(n,label,body):
 text(f'<font color="#087F82"><b>{n:02d}</b></font>  <b>{label}</b><br/>{body}')
def box(label,body):
 t=Table([[p(label,'subtitle')],[p(body)]],colWidths=[WIDTH-20])
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),PALE),('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),10),('TOPPADDING',(0,0),(-1,0),1),('BOTTOMPADDING',(0,-1),(-1,-1),7)]))
 items.append(KeepTogether([t,Spacer(1,10)]))
def shot(name,caption,width=WIDTH):
 img=Image(str(HERE/'imagens'/name),width=width,height=width*600/760)
 img.hAlign='CENTER'
 items.append(KeepTogether([img,p(caption,'caption')]))
def table(headers,rows,widths):
 data=[[p(h,'headcell') for h in headers]]+[[p(c,'cell') for c in row] for row in rows]
 t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),TEAL),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F3F6F7')]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),9),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8),('LINEBELOW',(0,0),(-1,0),.6,TEAL)]))
 items.append(t);space(9)

# 1 — Cover.
text('COLMEIA  /  REALIDADE AUMENTADA','kicker');space(19)
text('Caixa de Areia','cover');text('Manual do painel Python','cover_sub')
text('Do enquadramento do Kinect à projeção: um guia ilustrado para operar pelos botões, abas e controles do painel.')
space(7)
shot('06_previa_projetor.png','Interface real do painel. A prévia fica no computador; o relevo é enviado ao projetor.',width=430)
text('<b>Gustavo Lass</b><br/>Bolsista do Colmeia<br/>Desenvolvimento do painel Python e das adaptações de integração; atualização deste manual.')
text('Edição atualizada • 25 de setembro de 2026','small')

# 2 — Start.
title(1,'Ligar e começar')
text('Este guia considera o computador do projeto com o painel instalado. Para o uso diário, não é necessário digitar argumentos do SARndbox.')
step(1,'Prepare a montagem','Ligue a alimentação do Kinect, conecte seu USB ao computador e conecte o projetor. Deixe os dois firmes, apontados para a caixa, com os quatro cantos visíveis ao sensor.')
step(2,'Configure a segunda tela','Nas configurações de telas do Linux, use <b>estender/unir as telas</b>. Mantenha o computador como tela principal e o projetor como segunda tela. Evite espelhamento, pois ele também exibiria o painel na areia.')
step(3,'Abra o painel','Abra <b>Atividades</b> ou o menu de aplicativos, pesquise <b>Painel da Caixa de Areia</b> e clique no resultado. Também há um atalho com esse nome na área de trabalho; se solicitado pelo Linux, use <b>Permitir iniciar</b>.')
step(4,'Inicie a projeção','No rodapé do painel, clique em <b>Aplicar e abrir a projeção</b>. Aguarde a imagem do Kinect e do relevo. Os últimos ajustes aplicados são carregados ao abrir o painel.')
box('Use o atalho do painel','O atalho antigo <b>Caixa de Areia</b> abre diretamente o programa anterior. Para seguir este manual, escolha <b>Painel da Caixa de Areia</b>. Feche outra instância do SARndbox, RawKinectViewer ou CalibrateProjector antes de iniciar a câmera.')
text('Onde encontrar cada ajuste','subtitle')
table(['Quero…','Página'],[
 ('Conhecer as abas e os botões','3'),('Ver a profundidade e marcar a área da caixa','4–5'),
 ('Regular fundo, nível azul/verde e topo','6'),('Girar, enquadrar e conferir a projeção','7–8'),
 ('Melhorar a resposta e resolver problemas','9–10'),('Entender a calibração, salvar e encerrar','11')],[WIDTH-65,65])

# 3 — UI.
title(2,'Conheça o painel')
shot('01_ajustes_alturas.png','Figura 1. Aba Ajustes e rodapé fixo. Os valores da captura pertencem a esta montagem; não são valores universais.')
table(['Parte da interface','Para que serve'],[
 ('<b>Ajustes</b>','Alturas, desempenho, aparência, giro, tamanho e recortes.'),
 ('<b>Prévia do projetor</b>','Cópia reduzida da imagem que está sendo enviada ao projetor.'),
 ('<b>Câmera do Kinect</b>','Profundidade usada no relevo e marcação da área; câmera colorida opcional.')],[135,WIDTH-135])
text('<b>Aplicar e abrir a projeção</b> salva e usa as alterações. Aplicar reinicia a projeção e <b>zera a água simulada</b>. O FPS e as mensagens ficam no rodapé do painel, fora da imagem projetada.')
text('Em 800 × 600, use a barra de rolagem da aba Ajustes para chegar aos controles inferiores. Os botões do rodapé permanecem acessíveis.','small')

# 4 — Sensor.
title(3,'Veja o sensor que mede a areia')
text('Abra <b>Câmera do Kinect</b>, mantenha <b>Ativar prévia</b> marcado, selecione <b>Profundidade (relevo)</b> e clique em <b>Aplicar</b>.')
shot('04_profundidade.png','Figura 2. Profundidade bruta do Kinect, antes do filtro e dos limites de altura.',width=WIDTH)
text('<b>Claro:</b> pontos mais próximos do Kinect. <b>Escuro:</b> pontos mais distantes. <b>Preto:</b> ausência de leitura. O contraste é automático: os tons não são uma régua em centímetros.')
text('Confira os <b>quatro cantos internos</b> da caixa. É normal o sensor enxergar também o chão ou o suporte. Na próxima etapa, você define qual parte será usada no relevo.')
box('Profundidade e Colorida são diferentes','<b>Profundidade (relevo)</b> é a imagem usada para marcar a área e medir as alturas. <b>Colorida</b> é uma fotografia da caixa e tem outro enquadramento. Para trocar o modo, selecione a opção e clique em Aplicar.')

# 5 — ROI.
title(4,'Desenhe a área útil da caixa')
shot('05_area_marcada.png','Figura 3. Exemplo de marcação por dentro das paredes. Os pontos verdes pertencem ao painel e não são projetados na areia.')
step(1,'Clique em Marcar 4 cantos','Na imagem de <b>Profundidade (relevo)</b>, clique nesta ordem: <b>1 superior esquerdo → 2 superior direito → 3 inferior direito → 4 inferior esquerdo</b>.')
step(2,'Ajuste o contorno','Arraste os pontos verdes até as bordas internas da areia. Deixe a faixa da parede fora da seleção. As linhas devem contornar a caixa sem se cruzar.')
step(3,'Clique em Aplicar','As alturas fora da área são ignoradas pela malha. A seleção fica salva. Sem matriz de calibração, a visão do relevo passa a enquadrar a área escolhida.')
text('A prévia de profundidade continua mostrando o sensor inteiro para permitir corrigir os cantos. Para retirar a seleção, clique em <b>Usar toda a captura</b> e depois em <b>Aplicar</b>.','small')
text('Aplicar uma área selecionada zera os recortes antigos de borda. A marcação usa o plano de referência já existente; não mede novamente o fundo da caixa.','small')

# 6 — Heights.
title(5,'Regule as alturas e as cores')
text('Na aba <b>Ajustes</b>, mova a barra ou digite o valor no campo à direita. Os valores são centímetros em relação ao plano de referência já medido.')
shot('01_ajustes_alturas.png','Figura 4. Fundo, nível azul/verde e topo: ajuste um controle de cada vez.',width=430)
table(['Controle','O que muda'],[
 ('<b>Fundo</b>','Menor altura aceita e início do azul escuro. Para aceitar depressões mais baixas, diminua o valor.'),
 ('<b>Nível azul/verde</b>','Desloca a transição das cores. Aumentar faz o azul alcançar alturas maiores; diminuir faz o azul recuar.'),
 ('<b>Topo</b>','Maior altura aceita e extremidade branca da paleta. Aumente para aceitar montes mais altos.')],[117,WIDTH-117])
text('<b>Experimente de 1 em 1 cm:</b> altere um valor, clique em Aplicar, faça um pequeno monte e um vale e observe o resultado. Mantenha sempre <b>Fundo &lt; Nível azul/verde &lt; Topo</b>.')
text('Fundo e topo também excluem leituras fora da faixa. O nível azul/verde muda a paleta; não altera o plano medido nem adiciona água à simulação.','small')

# 7 — Frame.
title(6,'Gire e enquadre a imagem')
shot('02_giro_enquadramento.png','Figura 5. Role a aba Ajustes para encontrar giro, enquadramento e recortes.',width=460)
text('<b>Girar imagem no sentido horário.</b> Use 0°, 90°, 180°, 270° ou a barra para outro ângulo. 360° volta à orientação inicial. Depois clique em Aplicar.')
text('<b>Tamanho da imagem (%).</b> Na visão manual, diminua para enxergar mais da caixa e aumente para aproximar. Comece perto de 100%; valores maiores podem cortar bordas. O botão <b>Afastar e remover recortes</b> coloca 75% e limpa as máscaras de borda, aguardando Aplicar.')
text('<b>Recortar paredes.</b> Esquerda, Direita, Cima e Baixo escondem faixas da imagem projetada. Esse recorte visual não define a área medida pelo Kinect. Para limitar a medição, use os quatro cantos da página 5.')
box('Se a caixa for quadrada','Uma área quadrada pode aparecer com faixas pretas numa tela retangular. Isso preserva as proporções. Marque a área interna e reduza o tamanho se algum lado ficar cortado. Girar e aumentar a imagem não substituem o alinhamento por calibração.')

# 8 — Projector.
title(7,'Confira o que será projetado')
shot('06_previa_projetor.png','Figura 6. Prévia da saída do projetor: relevo, curvas e cores. Controles e FPS ficam somente no painel.')
step(1,'Confira a segunda tela','Com uma única tela externa ativa, o painel tenta abrir a projeção nela em tela cheia. Se abrir na tela errada, mova a janela do SARndbox para o projetor e pressione <b>F11</b>.')
step(2,'Compare sensor e saída','A aba <b>Câmera do Kinect</b> mostra a área capturada. A aba <b>Prévia do projetor</b> mostra o relevo desenhado após os ajustes. Elas têm enquadramentos diferentes.')
step(3,'Verifique o encaixe sobre a areia','Faça um monte e observe se as cores acompanham sua posição física. Se houver deslocamento mesmo com a área e o giro corretos, confira a calibração com o responsável técnico.')
text('As miniaturas atualizam até 5 imagens/s. O contador do rodapé mede a projeção, que pode estar a aproximadamente 30 FPS mesmo quando a prévia parece menos fluida.','small')

# 9 — Performance.
title(8,'Aparência e resposta ao movimento')
text('Na aba <b>Ajustes</b>, escolha um perfil em <b>Desempenho</b> e clique em <b>Aplicar</b>. Comece por <b>Resposta rápida</b>.')
table(['Perfil','Quando usar','Efeito'],[
 ('<b>Resposta rápida</b>','Uso normal e areia mudando de forma.','Filtro mais curto; mantém os detalhes da água.'),
 ('<b>Mais leve</b>','A projeção está com FPS baixo.','Reduz a grade e o trabalho da simulação de água.'),
 ('<b>Mais suave</b>','A superfície ou as curvas ficam tremendo.','Suaviza mais; pode acrescentar atraso na resposta.'),
 ('<b>Perfil do manual</b>','Comparar com o comportamento anterior.','Filtro mais longo, que demora mais a acompanhar mudanças.')],[125,175,WIDTH-300])
text('Se parece estar “lagando”','subtitle')
step(1,'Olhe o FPS do rodapé','FPS baixo sugere dificuldade para desenhar ou simular. Experimente Mais leve e feche outros aplicativos pesados.')
step(2,'Observe o atraso da areia','Se o FPS está normal, mas o relevo demora a mudar, prefira Resposta rápida. Um filtro mais suave pode parecer lento mesmo com boa taxa de desenho.')
step(3,'Confira a captura','Na profundidade, verifique se a areia aparece com leitura contínua. Pontos pretos indicam falta de dados. Confira posição do sensor, alimentação e cabos se a imagem desaparecer.')
text('Aparência do modo normal','subtitle')
text('Mantenha <b>Sombreamento do relevo</b> para destacar as formas e <b>Curvas de nível</b> para mostrar as linhas topográficas. Ligue ou desligue essas opções e clique em Aplicar para comparar.')
box('Não confunda prévia com desempenho','A miniatura tem atualização reduzida para aliviar a carga. No teste desta montagem, o painel registrou valores próximos de 30 FPS; isso não garante a mesma taxa em outra cena ou computador. A água reinicia sempre que você aplica ajustes.')

# 10 — Troubleshooting.
title(9,'Quando algo não funciona')
table(['O que aconteceu','O que fazer pela interface ou na montagem'],[
 ('A câmera não aparece.','Confira alimentação e USB do Kinect. Feche outros programas que usem o sensor e clique em <b>Aplicar</b> novamente. Leia a mensagem no rodapé.'),
 ('A câmera aparece colorida.','Escolha <b>Profundidade (relevo)</b> e clique em Aplicar para ver as medições e marcar a área.'),
 ('Marcar 4 cantos não inicia.','Ative a prévia e aplique o modo Profundidade. Aguarde uma imagem recente. Clique dentro da imagem, não nas margens pretas.'),
 ('Aparecem paredes no relevo.','Refaça ou arraste os quatro pontos para <b>dentro</b> das paredes e aplique. O sensor pode continuar mostrando o exterior; o contorno define a parte usada.'),
 ('Corta em cima ou embaixo.','Confira se os cantos estão visíveis no sensor. Se estiverem, marque a área e reduza <b>Tamanho da imagem</b>. Se não estiverem, reposicione o Kinect e revise a calibração.'),
 ('A caixa fica pequena ou há faixas pretas.','A área quadrada mantém sua proporção na tela retangular. Ajuste Tamanho aos poucos. Aumentar demais pode cortar bordas.'),
 ('Azul demais ou de menos.','Ajuste <b>Nível azul/verde</b>: diminua para o azul recuar; aumente para subir. Mantenha esse valor entre Fundo e Topo.'),
 ('Os botões sumiram em 800 × 600.','Use a barra de rolagem na aba Ajustes. Os botões Aplicar e Restaurar ficam fixos no rodapé; maximize o painel se necessário.'),
 ('O painel ou o FPS aparecem na areia.','Confira se o Linux está em <b>telas estendidas</b>. Deixe o painel no computador e apenas a janela do SARndbox no projetor.'),
 ('A projeção não acompanha os montes na posição certa.','Reveja a calibração física do projetor. A seleção da área limita a leitura, mas não corrige sozinha o alinhamento entre Kinect, areia e projetor.')],[152,WIDTH-152])
text('Se a projeção encerrar com erro, use a mensagem do rodapé para identificar a causa. O registro técnico fica na pasta <b>ajuste_altura</b>, no arquivo <b>sarndbox.log</b>.','small')

# 11 — Finish, boundary, provenance.
title(10,'Salvar, encerrar e manter a montagem')
step(1,'Salve os ajustes que funcionaram','Clique em <b>Aplicar</b>. O painel salva alturas, aparência, giro, tamanho, perfil de desempenho, modo da câmera e seleção da área. Alterar um controle sem aplicar não salva essa alteração.')
step(2,'Encerre pelo painel','Feche a janela do painel para encerrar a projeção iniciada por ele. Na próxima abertura, os últimos ajustes aplicados serão carregados; clique em Aplicar para iniciar novamente.')
step(3,'Restaure só quando necessário','<b>Restaurar valores iniciais</b> redefine os controles no painel, inclusive a seleção de área. A mudança só passa a valer ao clicar em Aplicar. Não é um botão para voltar ao ajuste anterior.')
box('O que ainda depende da calibração','O painel usa o <b>plano de referência da caixa</b> já medido. Marcar os cantos atualiza a área útil sobre esse plano. A <b>calibração do projetor</b> é outra etapa, necessária para fazer a imagem coincidir fisicamente com a areia. Se Kinect, projetor ou caixa forem movidos, revise a calibração. Se o rodapé mostrar “PRÉVIA… falta calibrar”, o sistema está usando orientação manual.')
text('Para quem cuida da instalação','subtitle')
text('Os ajustes locais ficam em <b>ajuste_altura/valores.json</b> e a seleção em <b>ajuste_altura/area_scan.txt</b>, dentro da pasta Kinect-3.10. Preserve também os arquivos de calibração originais. A instalação e a calibração inicial ficam sob responsabilidade técnica; os detalhes estão em <b>GUIA_CALIBRACAO_PROJETOR.md</b> e <b>AJUSTAR_ALTURA.md</b>.','small')
text('Autoria e créditos','subtitle')
text('<b>Gustavo Lass — bolsista do Colmeia.</b><br/>Desenvolvimento do painel Python e das adaptações de integração para ajustes, prévias, seleção da área do Kinect e controle da projeção. Atualização do manual de uso pela interface.')
text('Base tecnológica: SARndbox 2.8, Kinect 3.10 e Vrui 8.0, de Oliver Kreylos / KeckCAVES, UC Davis. Os créditos dos projetos originais são preservados; a autoria acima se refere ao painel e à adaptação local.','small')
text('Esta edição atualiza o manual “Caixa de Areia — Colmeia”, de 22 de abril de 2024, fornecido em Manual Caixa de Areia.pdf. O foco passa da operação por comandos para o uso do painel instalado. Capturas reais da interface; os valores e o contorno ilustrados devem ser ajustados para cada montagem.','small')
text('Versão do manual: 25/09/2026 • Uso pelo painel Python • Colmeia','small')

class ManualDoc(SimpleDocTemplate):
    def afterFlowable(self, flowable):
        if hasattr(flowable,'_bookmark'):
            self.canv.bookmarkPage(flowable._bookmark)
            self.canv.addOutlineEntry(flowable.getPlainText(),flowable._bookmark,0)

def furniture(c,doc):
    w,h=A4
    c.saveState()
    c.setStrokeColor(LINE);c.setLineWidth(.6)
    c.line(44,40,w-44,40)
    c.setFillColor(MUTED);c.setFont('Lato',8)
    c.drawString(44,27,'COLMEIA  •  MANUAL DO PAINEL PYTHON')
    c.drawRightString(w-44,27,str(doc.page))
    if doc.page>1:
        c.setFont('LatoBold',8);c.setFillColor(TEAL)
        c.drawString(44,h-32,'CAIXA DE AREIA  /  USO PELA INTERFACE')
        c.setFillColor(MUTED);c.setFont('Lato',8)
        c.drawRightString(w-44,h-32,'Gustavo Lass · Colmeia')
    c.restoreState()

doc=ManualDoc(str(OUT),pagesize=A4,rightMargin=44,leftMargin=44,topMargin=53,bottomMargin=53,
              title='Caixa de Areia — Manual do painel Python',author='Gustavo Lass — bolsista do Colmeia',
              subject='Guia ilustrado: operação pela interface, Kinect, seleção de área e projeção')
doc.build(items,onFirstPage=furniture,onLaterPages=furniture)
print(OUT)
