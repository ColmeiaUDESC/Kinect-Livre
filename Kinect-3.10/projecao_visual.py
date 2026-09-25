"""Aparência e orientação do SARndbox, sem alterar a calibração original."""
import math
import re
import struct
import subprocess

DEFAULTS = {'rotacao': 0.0, 'relevo': True, 'curvas': True}
# Perfil de água e chuva mostrado no manual enviado pelo usuário.
WATER_OPTIONS = ['-wo', '1.0', '-ws', '1.0', '5', '-wts', '320', '240', '-rs', '1.5']


def rotation_terms(degrees):
    if not math.isfinite(degrees):
        raise ValueError('Digite um ângulo válido.')
    angle = math.radians(degrees % 360)
    return round(math.cos(angle), 15), round(math.sin(angle), 15)


def rotated_projection(data, degrees, aspect):
    """Rotação horária em pixels centrada na imagem; mantém Z e perspectiva."""
    if len(data) != 128 or not math.isfinite(aspect) or aspect <= 0:
        raise ValueError('Matriz de calibração ou proporção de tela inválida.')
    matrix = struct.unpack('<16d', data)
    if not all(math.isfinite(v) for v in matrix):
        raise ValueError('A calibração contém números inválidos; refaça a calibração.')
    c, s = rotation_terms(degrees)
    if degrees % 360 == 0:
        return data
    result = list(matrix)
    for j in range(4):
        result[j] = c * matrix[j] + s / aspect * matrix[4 + j]
        result[4 + j] = -s * aspect * matrix[j] + c * matrix[4 + j]
    return struct.pack('<16d', *result)


def preview_view(layout, degrees, size_percent=100):
    """Arquivo Vrui v1.0: centro, raio, direção e vetor para cima (10 doubles)."""
    if not math.isfinite(size_percent) or not 40 <= size_percent <= 150:
        raise ValueError('O tamanho da imagem deve ficar entre 40 e 150%.')
    lines = [line for line in layout.splitlines() if line.strip()]
    pattern = r'[-+]?(?:\d*\.\d+|\d+\.?\d*)(?:[eE][-+]?\d+)?'
    rows = [[float(v) for v in re.findall(pattern, line)] for line in lines]
    if len(rows) != 5 or [len(row) for row in rows] != [4, 3, 3, 3, 3]:
        raise ValueError('BoxLayout precisa conter o plano e os quatro cantos.')
    if not all(math.isfinite(v) for row in rows for v in row):
        raise ValueError('BoxLayout contém números inválidos.')
    dot = lambda a, b: sum(x * y for x, y in zip(a, b))
    def unit(vector):
        length = math.sqrt(dot(vector, vector))
        if length < 1e-10:
            raise ValueError('Plano ou cantos degenerados no BoxLayout.')
        return [v / length for v in vector]
    normal = unit(rows[0][:3])
    offset = rows[0][3] / math.sqrt(dot(rows[0][:3], rows[0][:3]))
    corners = [[v - (dot(point, normal) - offset) * n for v, n in zip(point, normal)]
               for point in rows[1:]]
    center = [sum(p[i] for p in corners) / 4 for i in range(3)]
    x = [corners[1][i] - corners[0][i] + corners[3][i] - corners[2][i] for i in range(3)]
    x = unit([v - dot(x, normal) * n for v, n in zip(x, normal)])
    y = [normal[1] * x[2] - normal[2] * x[1],
         normal[2] * x[0] - normal[0] * x[2], normal[0] * x[1] - normal[1] * x[0]]
    size = max(math.sqrt(sum((p[i] - center[i]) ** 2 for i in range(3))) for p in corners)
    if size <= 0:
        raise ValueError('A caixa não tem tamanho válido.')
    size *= 100 / size_percent
    c, s = rotation_terms(degrees)
    up = [-s * a + c * b for a, b in zip(x, y)]
    return b'Vrui viewpoint file v1.0\n' + struct.pack('<10d', *center, size, *[-n for n in normal], *up)


def screen_aspect(output):
    try:
        result = subprocess.run(['xrandr', '--query'], capture_output=True,
                                text=True, timeout=3, check=True)
        for line in result.stdout.splitlines():
            if ((output and line.startswith(output + ' connected'))
                    or (not output and ' connected primary ' in line)):
                match = re.search(r'(\d+)x(\d+)\+', line)
                if match:
                    return int(match[1]) / int(match[2])
    except (OSError, subprocess.SubprocessError):
        pass
    raise ValueError('Não foi possível determinar a resolução da tela para girar a calibração.')


def appearance_options(visual):
    return ['-uhs' if visual['relevo'] else '-nhs', '-ucl' if visual['curvas'] else '-ncl']


def orientation_options(config, state, visual, output):
    matrix = config / 'ProjectorMatrix.dat'
    if matrix.is_file():
        data = matrix.read_bytes()
        rotated = rotated_projection(data, visual['rotacao'],
                                     screen_aspect(output) if visual['rotacao'] % 360 else 1)
        derived = state / 'ProjectorMatrix-rotacao.dat'
        derived.write_bytes(rotated)
        return ['-fpv', str(derived)], 'Projeção com calibração e rotação escolhida.'
    view = state / 'Orientacao.v1'
    view.write_bytes(preview_view((config / 'BoxLayout.txt').read_text(), visual['rotacao'], visual.get('tamanho', 100)))
    return ['-loadView', str(view)], 'PRÉVIA: orientação manual; falta calibrar o projetor para alinhar com a areia.'


CROP_DEFAULTS = {'esquerda': 0.0, 'direita': 0.0, 'cima': 0.0, 'baixo': 0.0}


def crop_options(crop):
    values = [float(crop[key]) for key in ('esquerda', 'direita', 'baixo', 'cima')]
    if not all(math.isfinite(value) and 0 <= value <= 45 for value in values):
        raise ValueError('Cada recorte deve ficar entre 0 e 45% da imagem.')
    return ['-crop', *[str(value) for value in values]]


PERFORMANCE_PROFILES = {
    'Resposta rápida': ('6', '3', '4', '320', '240', '5'),
    'Mais leve': ('6', '3', '4', '160', '120', '3'),
    'Mais suave': ('15', '5', '2', '320', '240', '5'),
    'Perfil do manual': ('30', '10', '2', '320', '240', '5'),
}


def performance_options(profile):
    if profile not in PERFORMANCE_PROFILES:
        raise ValueError('Escolha um modo de desempenho da lista.')
    slots, samples, variance, width, height, steps = PERFORMANCE_PROFILES[profile]
    return ['-wo', '1.0', '-ws', '1.0', steps, '-wts', width, height, '-rs', '1.5',
            '-nas', slots, '-sp', samples, variance]
