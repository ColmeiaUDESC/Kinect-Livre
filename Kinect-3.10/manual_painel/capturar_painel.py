"""Captura janelas reais do Tk com as prévias atuais, sem iniciar outra captura Kinect."""
from pathlib import Path
import struct
import subprocess
import sys
import time
import tkinter as tk
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import regular_altura as app

OUT=Path(__file__).resolve().parent/'imagens'
OUT.mkdir(exist_ok=True)
root=tk.Tk();panel=app.Panel(root)
root.geometry('760x600+70+60')
class ExistingProjection:
    def poll(self):return None
panel.process=ExistingProjection()
panel.active_camera_mode='Profundidade (relevo)'
panel.camera_label.editable=True
panel.status.set('PRÉVIA: orientação manual; falta calibrar o projetor para alinhar com a areia.')

def update():
    for _ in range(4):
        root.update();time.sleep(.1)
    panel.poll_preview();root.update()

def capture(name):
    update()
    path=OUT/(name+'.xwd')
    subprocess.run(['xwd','-silent','-id',str(root.winfo_id()),'-out',str(path)],check=True,timeout=5)
    blob=path.read_bytes();h=struct.unpack('>25I',blob[:100])
    assert h[11]==32 and h[14:17]==(0xff0000,0xff00,0xff)
    image=Image.frombytes('RGB',(h[4],h[5]),blob[h[0]+h[19]*12:],'raw','BGRX',h[12],1)
    image.save(OUT/(name+'.png'));path.unlink()
    print(name,image.size)
try:
    panel.notebook.select(0);panel.canvas.yview_moveto(0);capture('01_ajustes_alturas')
    panel.canvas.yview_moveto(.43);capture('02_giro_enquadramento')
    panel.canvas.yview_moveto(1);capture('03_recortes')
    panel.notebook.select(panel.camera_page)
    panel.camera_label.points=[]
    panel.area_hint.set('Marque as bordas internas da caixa; arraste os pontos para ajustar.')
    capture('04_profundidade')
    # Reorder the existing contour for the documented clockwise click sequence.
    points=panel.scan_points
    if len(points)==4:
        start=min(range(4),key=lambda i:points[i][0]+points[i][1])
        points=points[start:]+points[:start]
    # Demonstration: inset the saved contour to keep the bright walls outside.
    points=[[.30,.18],[.83,.18],[.84,.89],[.30,.89]]
    panel.camera_label.points=[p[:] for p in points]
    panel.scan_area_changed(points);panel.camera_label.redraw()
    capture('05_area_marcada')
    panel.notebook.select(panel.preview_page);capture('06_previa_projetor')
finally:
    panel.process=None
    panel.close()
