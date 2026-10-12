# PyInstaller onedir distribution for Windows. Run: pyinstaller ActivityTracker.spec
from PyInstaller.utils.hooks import collect_all, collect_submodules

datas = [('templates', 'templates'), ('static', 'static'), ('migrations', 'migrations')]
binaries = []
hiddenimports = collect_submodules('app') + collect_submodules('reportlab')
for package in ('xhtml2pdf', 'alembic'):
    extra_data, extra_binaries, extra_imports = collect_all(package)
    datas += extra_data
    binaries += extra_binaries
    hiddenimports += extra_imports
analysis = Analysis(['desktop_app.py'], pathex=[], binaries=binaries, datas=datas,
                    hiddenimports=hiddenimports, hookspath=[], runtime_hooks=[], excludes=[])
pyz = PYZ(analysis.pure)
exe = EXE(pyz, analysis.scripts, [], exclude_binaries=True, name='ActivityTracker', console=True)
coll = COLLECT(exe, analysis.binaries, analysis.datas, name='ActivityTracker')
