from dlg.apps.bash_shell_app import BashShellApp
from dlg.exceptions import InvalidDropException


class CImagerDrop(BashShellApp):

    IMAGER_CMD = 'cimager'

    def initialize(self, **kwargs):
        self.config_file = self._getArg(kwargs, 'config', None)
        if not self.config_file:
            raise InvalidDropException(self, 'No config specified, cannot create CImageDrop')

        kwargs['command'] = '{0} -c {1}'.format(self.IMAGER_CMD, self.config_file)

        super(BashShellApp, self).initialize(**kwargs)
