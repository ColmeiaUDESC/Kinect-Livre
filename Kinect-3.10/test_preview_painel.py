import json
import os
from pathlib import Path
import tempfile
import time
import tkinter as tk
import unittest
from unittest.mock import patch
import regular_altura as app
import projecao_visual as visual


class PreviewTests(unittest.TestCase):
    def test_response_profile_preserves_water_and_reduces_filter(self):
        args=visual.performance_options('Resposta rápida')
        self.assertEqual(args[args.index('-nas')+1], '6')
        self.assertEqual(args[args.index('-wts')+1:args.index('-wts')+3], ['320','240'])
        self.assertEqual(args[args.index('-ws')+1:args.index('-ws')+3], ['1.0','5'])
        for profile in visual.PERFORMANCE_PROFILES:
            args=visual.performance_options(profile)
            self.assertLessEqual(int(args[args.index('-sp')+1]), int(args[args.index('-nas')+1]))
        with self.assertRaises(ValueError):visual.performance_options('inválido')

    def test_preview_loads_with_fixed_footer_at_small_resolution(self):
        with tempfile.TemporaryDirectory() as directory:
            state=Path(directory)
            with patch.object(app,'STATE',state):
                root=tk.Tk()
                panel=app.Panel(root)
                try:
                    root.geometry('650x480+20+40')
                    panel.notebook.select(panel.preview_page)
                    root.update()
                    # Known top/red and bottom/blue PPM tests Tk's binary loader.
                    pixels=b'\xff\x00\x00'*4+b'\x00\x00\xff'*4
                    panel.preview_file.write_bytes(b'P6\n4 2\n255\n'+pixels)
                    Path(str(panel.preview_file)+'.json').write_text(json.dumps({'fps':29.8,'preview_supported':True}))
                    class Running:
                        def poll(self):return None
                    panel.process=Running()
                    panel.poll_preview()
                    root.update()
                    self.assertEqual(panel.preview_image.get(0,0),(255,0,0))
                    self.assertEqual(panel.preview_image.get(0,1),(0,0,255))
                    self.assertIn('29.8 FPS',panel.fps_status.get())
                    y=panel.apply_button.winfo_rooty()-root.winfo_rooty()
                    self.assertLessEqual(y+panel.apply_button.winfo_height(),root.winfo_height())
                    self.assertEqual(panel.performance.get(),'Resposta rápida')
                    panel.process=None
                finally:
                    panel.close()

    def test_camera_without_projector_metrics_and_stale_frame(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(app, 'STATE', Path(directory)):
                root = tk.Tk()
                panel = app.Panel(root)
                class Running:
                    def poll(self): return None
                try:
                    panel.notebook.select(panel.camera_page)
                    root.update()
                    panel.process = Running()
                    panel.camera_file.write_bytes(b'P6\n1 2\n255\n'+bytes([255,0,0,0,0,255]))
                    panel.poll_preview()
                    self.assertEqual(panel.camera_image.get(0,0),(255,0,0))
                    self.assertEqual(panel.camera_image.get(0,1),(0,0,255))
                    os.utime(panel.camera_file,(time.time()-10,time.time()-10))
                    panel.poll_preview()
                    self.assertIsNone(panel.camera_image)
                    self.assertIn('Sem imagem recente',panel.camera_label.cget('text'))
                    panel.active_camera = False
                    panel.poll_preview()
                    self.assertIn('desativada',panel.camera_label.cget('text'))
                    y = panel.apply_button.winfo_rooty()-root.winfo_rooty()
                    self.assertLessEqual(y+panel.apply_button.winfo_height(),root.winfo_height())
                finally:
                    panel.process = None
                    panel.close()

    def test_one_process_command_contains_preview_and_projector_output(self):
        with tempfile.TemporaryDirectory() as directory:
            state=Path(directory)
            (state/'native/bin').mkdir(parents=True)
            (state/'native/bin/SARndbox').symlink_to(app.STATE/'native/bin/SARndbox')
            with patch.object(app,'STATE',state),patch.object(app,'external_output',return_value='PROJECTOR'):
                root=tk.Tk();root.withdraw();panel=app.Panel(root)
                commands=[]
                panel.start_when_stopped=lambda cmd:commands.append(cmd)
                try:
                    panel.apply();time.sleep(.15);root.update()
                    self.assertEqual(len(commands),1)
                    command=commands[0]
                    self.assertIn('-panelPreview',command)
                    self.assertIn('-cameraDepthPreview',command)
                    self.assertNotIn('-cameraPreview',command)
                    self.assertEqual(command[command.index('-cameraDepthPreview')+1],str(panel.camera_file))
                    self.assertIn('Window/outputName=PROJECTOR',command)
                    self.assertIn('Window/windowFullscreen=true',command)
                    self.assertEqual(command[command.index('-nas')+1],'6')
                    self.assertEqual(command[command.index('-wts')+1:command.index('-wts')+3],['320','240'])
                    saved=json.loads((state/'valores.json').read_text())
                    self.assertEqual(saved['desempenho'],'Resposta rápida')
                finally:panel.close()


if __name__=='__main__':unittest.main()
