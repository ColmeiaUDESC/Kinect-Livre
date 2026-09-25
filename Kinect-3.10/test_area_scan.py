import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import tkinter as tk
import time
import unittest
from unittest.mock import patch
from area_scan import SensorCanvas, validate_area
import regular_altura as app

POINTS = [[.2,.2],[.8,.2],[.8,.8],[.2,.8]]

class AreaTests(unittest.TestCase):
    def test_reject_crossing_and_tiny_area(self):
        validate_area(POINTS)
        validate_area(list(reversed(POINTS)))
        validate_area([])
        for points in ([POINTS[i] for i in (0,2,1,3)], POINTS[:3],
                       [[0,0],[.001,0],[.001,.001],[0,.001]],
                       [[-1,0],[1,0],[1,1],[0,1]]):
            with self.assertRaises(ValueError): validate_area(points)

    def test_click_drag_resize_keeps_depth_coordinates(self):
        root = tk.Tk()
        try:
            root.geometry('500x300')
            observed = []
            canvas = SensorCanvas(root, lambda points: observed.append([p[:] for p in points]))
            canvas.pack(fill='both',expand=True)
            photo = tk.PhotoImage(width=320,height=240)
            canvas.configure(image=photo,text='')
            canvas.editable = True
            root.update()
            x,y,w,h = canvas.image_rect
            canvas.press(SimpleNamespace(x=0,y=0)) # Black margin is not sensor data.
            self.assertEqual(canvas.points,[])
            for u,v in POINTS:
                canvas.press(SimpleNamespace(x=x+u*w,y=y+v*h))
            validate_area(canvas.points)
            canvas.press(SimpleNamespace(x=x+.2*w,y=y+.2*h))
            canvas.move(SimpleNamespace(x=x+.25*w,y=y+.3*h))
            self.assertAlmostEqual(canvas.points[0][0],.25)
            self.assertAlmostEqual(canvas.points[0][1],.3)
            before = [p[:] for p in canvas.points]
            root.geometry('650x480');root.update()
            self.assertEqual(canvas.points,before)
            x,y,w,h = canvas.image_rect
            self.assertGreaterEqual(x,0);self.assertGreaterEqual(y,0)
            self.assertLessEqual(y+h,canvas.winfo_height())
        finally:root.destroy()

    def test_selected_area_saved_and_passed_without_old_black_bands(self):
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory)
            (state/'native/bin').mkdir(parents=True)
            (state/'native/bin/SARndbox').symlink_to(app.STATE/'native/bin/SARndbox')
            with patch.object(app,'STATE',state),patch.object(app,'external_output',return_value='PROJECTOR'):
                root=tk.Tk();root.withdraw();panel=app.Panel(root)
                commands=[]
                panel.start_when_stopped=lambda cmd:commands.append(cmd)
                try:
                    panel.scan_points=POINTS
                    panel.crop['esquerda'].set(20)
                    panel.apply();time.sleep(.15);root.update()
                    command=commands[0]
                    self.assertIn('-scanArea',command)
                    self.assertIn('-scanView',command)
                    self.assertNotIn('-crop',command)
                    self.assertIn('-cameraDepthPreview',command)
                    saved=json.loads((state/'valores.json').read_text())
                    self.assertEqual(saved['area_scan'],POINTS)
                    self.assertTrue((state/'area_scan.txt').is_file())
                    panel.applying=False
                    panel.clear_scan_area()
                    panel.camera_mode.set('Colorida')
                    panel.apply();time.sleep(.15);root.update()
                    self.assertNotIn('-scanArea',commands[1])
                    self.assertIn('-cameraPreview',commands[1])
                finally:panel.close()

if __name__=='__main__':unittest.main()
