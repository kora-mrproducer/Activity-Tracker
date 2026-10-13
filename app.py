"""Compatibility launcher: use the maintained application factory and local server."""
if __name__ == '__main__':
    import runpy
    runpy.run_module('run', run_name='__main__')
