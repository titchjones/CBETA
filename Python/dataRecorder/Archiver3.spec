# -*- mode: python -*-

block_cipher = None


a = Analysis(['archiver.py'],
             pathex=['F:\\BMAD\\CBETA\\Python\\dataRecorder'],
             binaries=[],
             datas=[ ("C:\Anaconda3\Lib\site-packages\epics\clibs\win64\ca.dll", '.'), ("C:\Anaconda3\Lib\site-packages\epics\clibs\win64\Com.dll",'.'), 
                     ("C:\Anaconda3\qt.conf", '.')],
             hiddenimports=['socket', 'epics', 'epics.clibs'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='Archiver3',
          debug=False,
          strip=False,
          upx=False,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='Archiver3')
