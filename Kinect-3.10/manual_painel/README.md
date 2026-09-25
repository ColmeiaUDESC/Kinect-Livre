# Manual do painel Python

PDF final: `../Manual Caixa de Areia - Painel Python.pdf`.
Também foi criada uma cópia na área de trabalho.

Base: `/home/colmeia/Desktop/backup-2025/Manual Caixa de Areia.pdf`, edição de 22/04/2024.
O arquivo original foi preservado.

- `gerar_manual.py`: conteúdo, diagramação e créditos; gera o PDF com ReportLab.
- `imagens/`: capturas reais das abas do painel Tk.
- `capturar_painel.py`: captura uma instância de documentação lendo as prévias do processo já ativo; não abre outro Kinect nem aplica mudanças. O contorno da figura de seleção é um exemplo ajustado dentro das paredes.
- `revisao/`: páginas renderizadas usadas na conferência visual.

Para atualizar a diagramação mantendo os prints: `python3 manual_painel/gerar_manual.py`.
Dependências usadas: Python 3, ReportLab, Pillow e fontes Lato. Para novas capturas: Tk e xwd; é necessário que a projeção já esteja gerando os arquivos de prévia.

Validação: 11 páginas A4; conferência visual das páginas; texto e metadados conferidos.
Autoria editorial e do desenvolvimento local conforme solicitado: Gustavo Lass, bolsista do Colmeia.
