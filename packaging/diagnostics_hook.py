"""CI-only startup diagnostics enabled by an explicit environment variable."""
import os
import sys
if os.environ.get('WINDOWS_APP_DIAGNOSTICS'):
    import faulthandler
    import traceback
    _diagnostic_stream=open(os.environ['WINDOWS_APP_DIAGNOSTICS'],'a',encoding='utf-8')
    _diagnostic_stream.write('Custom runtime hook started\n');_diagnostic_stream.flush()
    faulthandler.enable(file=_diagnostic_stream)
    faulthandler.dump_traceback_later(15,repeat=True,file=_diagnostic_stream)
    def _diagnostic_exception(kind,error,tb):
        traceback.print_exception(kind,error,tb,file=_diagnostic_stream)
        _diagnostic_stream.flush()
        os._exit(1)
    sys.excepthook=_diagnostic_exception
