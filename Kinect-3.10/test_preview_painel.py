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
            with patch.object(app,'STATE',state),patch.object(app,'external_output',return_value='PROJECTOR'),patch.object(app,'kinect_status',return_value='ok'),patch.object(app,'kinect_users',return_value={}):
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


    def test_kinect_status_reads_usb_devices(self):
        with tempfile.TemporaryDirectory() as directory:
            usb=Path(directory)
            def device(name,vendor,product):
                (usb/name).mkdir();(usb/name/'idVendor').write_text(vendor+'\n');(usb/name/'idProduct').write_text(product+'\n')
            (usb/'usb1').mkdir()
            device('1-1','1d6b','0002')
            self.assertEqual(app.kinect_status(usb),'ausente')
            device('1-2','045e','02b0')
            self.assertEqual(app.kinect_status(usb),'sem_energia')
            device('1-3','045e','02ae')
            self.assertEqual(app.kinect_status(usb),'ok')
            self.assertIsNone(app.kinect_status(usb/'inexistente'))

    def fake_install(self,directory):
        """Instalação mínima do SARndbox, para testar sem depender da máquina."""
        state=Path(directory)
        (state/'native/bin').mkdir(parents=True)
        (state/'native/bin/SARndbox').touch()
        config=state/'config';config.mkdir()
        (config/'HeightColorMap.cpt').write_text('-10 0 0 255\n10 255 255 255\n')
        return state,config

    def test_waits_for_kinect_and_starts_when_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            state,config=self.fake_install(directory)
            status={'value':'ausente'}
            with patch.object(app,'STATE',state),patch.object(app,'CONFIG',config),patch.object(app,'external_output',return_value=None),patch.object(app,'kinect_status',lambda:status['value']),\
                 patch.object(app,'kinect_users',return_value={}),\
                 patch.object(app.visual_tools,'orientation_options',return_value=([],'')),\
                 patch.object(app.messagebox,'showerror',side_effect=AssertionError):
                root=tk.Tk();root.withdraw();panel=app.Panel(root)
                commands=[]
                panel.start_when_stopped=lambda cmd:commands.append(cmd)
                try:
                    root.update()
                    self.assertEqual(panel.kinect_warning.winfo_manager(),'pack')
                    panel.apply();time.sleep(.15);root.update()
                    self.assertEqual(commands,[])
                    self.assertTrue(panel.waiting_kinect)
                    self.assertEqual(panel.cancel_button.winfo_manager(),'pack')
                    self.assertIn('Aguardando o Kinect',panel.status.get())
                    status['value']='ok'
                    panel.watch_kinect();root.update()
                    self.assertEqual(panel.kinect_warning.winfo_manager(),'')
                    self.assertIn('Kinect disponível',panel.status.get())
                    panel.start_after_kinect();time.sleep(.15);root.update()
                    self.assertEqual(len(commands),1)
                    self.assertFalse(panel.waiting_kinect)
                    self.assertEqual(panel.cancel_button.winfo_manager(),'')
                finally:panel.close()

    def test_cancel_wait_does_not_start_later(self):
        with tempfile.TemporaryDirectory() as directory:
            state,config=self.fake_install(directory)
            status={'value':'ausente'}
            with patch.object(app,'STATE',state),patch.object(app,'CONFIG',config),patch.object(app,'external_output',return_value=None),patch.object(app,'kinect_status',lambda:status['value']),\
                 patch.object(app,'kinect_users',return_value={}),\
                 patch.object(app.visual_tools,'orientation_options',return_value=([],'')),\
                 patch.object(app.messagebox,'showerror',side_effect=AssertionError):
                root=tk.Tk();root.withdraw();panel=app.Panel(root)
                commands=[]
                panel.start_when_stopped=lambda cmd:commands.append(cmd)
                try:
                    panel.apply();root.update()
                    panel.cancel_wait()
                    status['value']='ok'
                    panel.watch_kinect();panel.start_after_kinect();time.sleep(.15);root.update()
                    self.assertEqual(commands,[])
                    self.assertIn('Clique em Aplicar',panel.status.get())
                finally:panel.close()

    def test_busy_kinect_asks_before_closing_other_program(self):
        with tempfile.TemporaryDirectory() as directory:
            state,config=self.fake_install(directory)
            users={4321:'RawKinectViewer'}
            with patch.object(app,'STATE',state),patch.object(app,'CONFIG',config),patch.object(app,'external_output',return_value=None),patch.object(app,'kinect_status',return_value='ok'),\
                 patch.object(app,'kinect_users',lambda ignore=():dict(users)),\
                 patch.object(app.visual_tools,'orientation_options',return_value=([],'')),\
                 patch.object(app.messagebox,'showerror',side_effect=AssertionError),\
                 patch.object(app.os,'kill') as kill:
                root=tk.Tk();root.withdraw();panel=app.Panel(root)
                commands=[]
                panel.start_when_stopped=lambda cmd:commands.append(cmd)
                try:
                    with patch.object(app.messagebox,'askyesno',return_value=False):
                        panel.apply();time.sleep(.15);root.update()
                    self.assertEqual(commands,[])
                    kill.assert_not_called()
                    self.assertFalse(panel.waiting_kinect)
                    self.assertIn('RawKinectViewer',panel.status.get())
                    with patch.object(app.messagebox,'askyesno',return_value=True):
                        panel.apply();time.sleep(.15);root.update()
                    kill.assert_called_once_with(4321,app.signal.SIGTERM)
                    self.assertTrue(panel.waiting_kinect)
                    # Enquanto o outro programa não fecha, não tenta abrir.
                    panel.watch_kinect();self.assertFalse(panel.start_scheduled)
                    users.clear()
                    panel.watch_kinect();self.assertTrue(panel.start_scheduled)
                    panel.start_after_kinect();time.sleep(.15);root.update()
                    self.assertEqual(len(commands),1)
                finally:panel.close()

    def test_stuck_projection_is_killed_after_timeout(self):
        class Stuck:
            pid=99999
            def __init__(self):self.killed=False
            def poll(self):return 0 if self.killed else None
            def terminate(self):pass
            def kill(self):self.killed=True
        with tempfile.TemporaryDirectory() as directory,patch.object(app,'STATE',Path(directory)),\
             patch.object(app,'STOP_TIMEOUT',0.05),patch.object(app,'kinect_status',return_value=None):
            root=tk.Tk();root.withdraw();panel=app.Panel(root)
            try:
                panel.process=stuck=Stuck()
                panel.stop_process()
                time.sleep(.2);root.update()
                self.assertTrue(stuck.killed)
            finally:
                panel.process=None
                panel.close()

    def test_kinect_users_reads_process_names(self):
        with tempfile.TemporaryDirectory() as directory:
            proc=Path(directory)
            for pid,name in ((10,'RawKinectViewer'),(11,'CalibrateProjec'),(12,'bash'),(13,'SARndbox')):
                (proc/str(pid)).mkdir();(proc/str(pid)/'comm').write_text(name+'\n')
            (proc/'self').mkdir()
            self.assertEqual(app.kinect_users(ignore={13},proc=proc),{10:'RawKinectViewer',11:'CalibrateProjector'})
            self.assertEqual(app.kinect_users(proc=proc/'inexistente'),{})

    def test_find_sandbox_keeps_original_location_first(self):
        with tempfile.TemporaryDirectory() as directory:
            base=Path(directory)
            root=base/'src'/'Kinect-3.10';root.mkdir(parents=True)
            home=base/'home'
            def install(path):
                (path/'etc'/'SARndbox-2.8').mkdir(parents=True);return path
            # Nada instalado: devolve o local original para a mensagem de erro.
            self.assertEqual(app.find_sandbox({},root,home),base/'src'/'SARndbox-2.8')
            other=install(home/'src'/'SARndbox-2.8')
            self.assertEqual(app.find_sandbox({},root,home),other)
            original=install(base/'src'/'SARndbox-2.8')
            self.assertEqual(app.find_sandbox({},root,home),original)
            self.assertEqual(app.find_sandbox({'SARNDBOX_DIR':str(other)},root,home),other)

if __name__=='__main__':unittest.main()
