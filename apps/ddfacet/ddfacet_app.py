from dlg.apps.bash_shell_app import BashShellApp
from dlg.meta import dlg_string_param, dlg_int_param, dlg_component, dlg_batch_input, \
    dlg_batch_output, dlg_streaming_input


class DDFacetApp(BashShellApp):

    DDF_CMD = 'DDF.py'

    compontent_meta = dlg_component('DDFacetApp', 'Faceting for direction-dependent spectral deconvolution',
                                    [dlg_batch_input('binary/*', [])],
                                    [dlg_batch_output('binary/*', [])],
                                    [dlg_streaming_input('binary/*')])

    data_ms = dlg_string_param('Data-MS', None)
    data_colname = dlg_string_param('Data-ColName', "CORRECTED_DATA")
    data_chunkhours = dlg_int_param('Data-ChunkHours', 0.0)

    def initialize(self, **kwargs):
        self.command = 'dummy'

        super(DDFacetApp, self).initialize(**kwargs)

    def run(self):
        self.command = '{0} ' \
                       '--Data-MS={1}' \
                       '--Data-ColName={2} ' \
                       '--Data-ChunkHours={3}'.format(self.DDF_CMD,
                                                      self.data_ms,
                                                      self.data_colname,
                                                      self.data_chunkhours)

        self._run_bash(self._inputs, self._outputs)
