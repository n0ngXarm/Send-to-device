from pathlib import Path
import subprocess
import tempfile
import threading
import unittest
from unittest.mock import patch
import zipfile
from send_to_device import core
import installer

class CoreTests(unittest.TestCase):
    def test_discovery_only_own_devices_and_requires_online_and_capability(self):
        peers = {}
        for n, online, owner in [(1, True, 10), (2, False, 10), (3, True, 10), (4, True, 20)]:
            peers[str(n)] = dict(HostName='duplicate', UserID=owner, Online=online, TailscaleIPs=[f'100.64.0.{n}'])
        rows = core.devices(dict(BackendState='Running', Self={'UserID':10}, Peer=peers), '100.64.0.1 one\n100.64.0.2 two\n100.64.0.4 friend')
        self.assertEqual([r['ready'] for r in rows], [True,False,False])
        self.assertEqual(len({r['ip'] for r in rows}),3)
        with self.assertRaises(RuntimeError): core.devices({'BackendState':'Stopped'}, '')

    def test_zip_unicode_empty_folders_original_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); folder=root/'ภาพ'; folder.mkdir(); (folder/'empty').mkdir()
            (folder/'space file.txt').write_bytes(b'original')
            core.archive(folder,root/'out.zip',threading.Event())
            with zipfile.ZipFile(root/'out.zip') as z:
                self.assertEqual(z.read('ภาพ/space file.txt'),b'original')
                self.assertIn('ภาพ/empty/',z.namelist())

    def test_cancel_archive(self):
        with tempfile.TemporaryDirectory() as d:
            event=threading.Event(); event.set()
            source=Path(d)/'folder'; source.mkdir()
            with self.assertRaises(core.Cancelled): core.archive(source,Path(d)/'out.zip',event)

    def test_filename_collision_with_zip(self):
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/'photos'; a.mkdir(); b=Path(d)/'photos.zip'; b.touch()
            with self.assertRaises(ValueError): core.validate([a,b])

    def test_settings_validate_and_corrupt_history(self):
        with tempfile.TemporaryDirectory() as d:
            state=core.State(Path(d)); state.save(dict(timeout_minutes=120,ready_only=True,last_target='100.64.0.1'))
            self.assertEqual(state.settings()['timeout_minutes'],120)
            (Path(d)/'settings.json').write_text('{broken')
            self.assertEqual(state.settings()['timeout_minutes'],30)
            (Path(d)/'history.jsonl').write_text('{broken\n')
            state.record(dict(name='phone',ip='100.64.0.1'),1,2,'cancelled')
            self.assertEqual(len(state.history()),1)

    def test_retry_never_resends_completed_file(self):
        target=dict(name='phone',ip='100.64.0.1',ready=True)
        with tempfile.TemporaryDirectory() as d:
            state=core.State(Path(d)/'state'); paths=[Path(d)/'a',Path(d)/'b']
            for path in paths: path.write_text('test')
            with patch.object(core,'discover',return_value=[target]), patch.object(core,'push',side_effect=[0,1,0]) as push:
                sent,result=core.transfer('mock',paths,target,state,threading.Event(),lambda *a:None,lambda *a:True)
            self.assertEqual([c.args[1].name for c in push.call_args_list],['a','b','b'])
            self.assertEqual((sent,result),(2,'สำเร็จ'))
            self.assertEqual(state.settings()['last_target'],target['ip'])
            self.assertEqual(state.history()[0]['sent'],2)

    def test_offline_recheck_blocks_send(self):
        target=dict(name='phone',ip='100.64.0.1',ready=True)
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'file'; path.touch(); state=core.State(Path(d)/'state')
            with patch.object(core,'discover',return_value=[dict(target,ready=False)]), patch.object(core,'push') as push:
                with self.assertRaises(RuntimeError): core.transfer('mock',[path],target,state,threading.Event(),lambda *a:None,lambda *a:True)
                push.assert_not_called()

    def test_lock_exclusion_and_release(self):
        with tempfile.TemporaryDirectory() as d:
            state=core.State(Path(d))
            with state.lock():
                with self.assertRaises(RuntimeError):
                    with state.lock(): pass
            with state.lock(): pass

    def test_install_and_uninstall_isolated(self):
        with tempfile.TemporaryDirectory() as d:
            target=Path(d)/'installed app with spaces'
            installer.install(target,shortcuts=False)
            self.assertTrue((target/'send_to_device/gui.py').exists())
            self.assertTrue((target/'install-manifest.json').exists())
            subprocess.run([__import__('sys').executable,'-c','from send_to_device import core'],cwd=target,check=True)
            installer.uninstall(target)
            self.assertFalse(target.exists())

    def test_timeout_and_cancel_stop_process(self):
        # Run a real child on every platform, substituting its command only.
        import sys
        original=subprocess.Popen; children=[]
        def spawn(*args,**kwargs):
            child=original([sys.executable,'-c','import time; time.sleep(60)'],**kwargs)
            children.append(child); return child
        with tempfile.TemporaryDirectory() as d, (Path(d)/'log').open('w') as log, patch.object(core.subprocess,'Popen',side_effect=spawn):
            result=core.push('mock',Path(d)/'file','100.64.0.1',log,threading.Event(),0)
            self.assertEqual(result,124); self.assertIsNotNone(children[-1].poll())
            event=threading.Event(); event.set()
            with self.assertRaises(core.Cancelled): core.push('mock',Path(d)/'file','100.64.0.1',log,event,60)
            self.assertIsNotNone(children[-1].poll())

if __name__=='__main__': unittest.main()
