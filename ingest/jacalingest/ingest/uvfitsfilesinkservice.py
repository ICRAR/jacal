from jacalingest.engine.service import Service

class UVFitsFileSinkService(Service):
    def __init__(self, messagingsystem, outputpath):
        super(UVFitsFileSinkService, self).__init__(messagingsystem)

        self.outputpath = outputpath

    def step(self):
        # code to write output to a UVFits file on the file system
        pass

