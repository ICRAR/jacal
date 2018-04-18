import logging
import os
import shutil
import subprocess
import sys
import time
import argparse

ICE_REGISTRY_CONFIG_TEMPLATE="""
#
# Registry Properties
#
IceGrid.Registry.Client.Endpoints=tcp -p 4061
IceGrid.Registry.Server.Endpoints=tcp
IceGrid.Registry.Internal.Endpoints=tcp
IceGrid.Registry.AdminPermissionsVerifier=IceGrid/NullPermissionsVerifier
IceGrid.Registry.Data={registrydatadirectory}
IceGrid.Registry.DynamicRegistration=1

# Disable IPv6 (as it is not enabled by default on Debian Lenny)
Ice.IPv6=0

#
# Network Tracing
#
# 0 = no network tracing
# 1 = trace connection establishment and closure
# 2 = like 1, but more detailed
# 3 = like 2, but also trace data transfer
#
Ice.Trace.Network=0

#
# Protocol Tracing
#
# 0 = no protocol tracing
# 1 = trace protocol messages
#
Ice.Trace.Protocol=0

Ice.IPv6=0
"""

ICE_GRID_ADMIN_CONFIG_TEMPLATE="""
# Node Properties
Ice.Default.Locator=IceGrid/Locator:tcp -p 4061

# Disable IPv6 (as it is not enabled by default on Debian Lenny)
Ice.IPv6=0
"""

ICE_STORM_CONFIG_TEMPLATE="""
# Registry location
Ice.Default.Locator=IceGrid/Locator:tcp -h localhost -p 4061

# Disable IPv6 (as it is not enabled by default on Debian Lenny)
Ice.IPv6=0

#
# IceBox Config
#

# Instance name
IceBox.InstanceName=IceStorm

# The IceStorm service
IceBox.Service.IceStorm=IceStormService,35:createIceStorm

# Services inherit icebox properties
IceBox.InheritProperties=1

#
# IceStorm Config
#

# The IceStorm service instance name
IceStorm.InstanceName=IceStorm

# Adapter config for IceStorm TopicManager
IceStorm.TopicManager.Endpoints=default
IceStorm.TopicManager.AdapterId=IceStorm.TopicManager

# Adapter config for IceStorm Publish
IceStorm.Publish.Endpoints=default
IceStorm.Publish.AdapterId=IceStorm.Publish

# Amount of time in milliseconds between flushes for batch mode
# transfer. The minimum allowable value is 100ms.
IceStorm.Flush.Timeout=500

# This property defines the home directory of the Freeze
# database environment for the IceStorm service.
Freeze.DbEnv.IceStorm.DbHome={dbdirectory}

# Increase maximum message size from default of 1MB to 128MB
Ice.MessageSizeMax=13107

# TopicManager Tracing
# 0 = no tracing
# 1 = trace topic creation, subscription, unsubscription
# 2 = like 1, but with more detailed subscription information
IceStorm.Trace.TopicManager=0

# Topic Tracing
# 0 = no tracing
# 1 = trace unsubscription diagnostics
IceStorm.Trace.Topic=0

# Subscriber Tracing
# 0 = no tracing
# 1 = subscriber diagnostics (subscription, unsubscription, event
#     propagation failures)
IceStorm.Trace.Subscriber=0
"""

def writeFromTemplate(path, template, params):
    with open(path, "w") as f:
        f.write(template.format(**params))
    
def writeIceRegistryConfig(path, params):
    writeFromTemplate(path, ICE_REGISTRY_CONFIG_TEMPLATE, params)
    
def writeIceGridAdminConfig(path, params):
    writeFromTemplate(path, ICE_GRID_ADMIN_CONFIG_TEMPLATE, params)
    
def writeIceStormConfig(path, params):
    writeFromTemplate(path, ICE_STORM_CONFIG_TEMPLATE, params)
    
def source(script):
    proc = subprocess.Popen(['bash', '-c', 'source %s && env' % script], stdout = subprocess.PIPE)
    for line in proc.stdout:
        (key, _, value) = line.partition("=")
        os.environ[key.strip()] = value.strip().strip()
    proc.communicate()
    
def waitIceRegistry(config):
    logging.info("Waiting for Ice Registry to start...")

    for i in range(10):
        time.sleep(1)
        try:
            output = subprocess.check_output(['icegridadmin', '--Ice.Config=%s' % config, '-u', 'foo', '-p', 'bar', '-e', 'registry list'])
        except subprocess.CalledProcessError:
            continue
        else:
            logging.info("Ice Registry started.")
            break
    else:
        logging.error("Ice Registry FAILED. Exiting.")
        sys.exit(1)

def waitIceStorm(config):
    logging.info("Waiting for IceStorm to start...")
    for i in range(10):
        time.sleep(1)
        try:
            output = subprocess.check_output(['icegridadmin', '--Ice.Config=%s' % config, '-u', 'foo', '-p', 'bar', '-e', 'adapter endpoints IceStorm.TopicManager'])
        except subprocess.CalledProcessError:
            continue
        else:
            if output == "<inactive>":
                continue
            else:
                logging.info("IceStorm started.")
                break
    else:
        logging.error("IceStorm FAILED. Exiting.")
        sys.exit(1)
    
class IceRunner(object):
    def __init__(self, workingdirectory):
        scriptdir = os.path.dirname(os.path.abspath(__file__))
        source('%s/init_package_env.sh' % scriptdir)
    
        if not os.path.exists(workingdirectory):
            os.mkdir(workingdirectory)
    
        self.datadirectory = "%s/ice_data" % workingdirectory
    
        if os.path.exists(self.datadirectory):
            shutil.rmtree(self.datadirectory)
        os.mkdir(self.datadirectory)
    
        self.iceRegistryConfigPath = "%s/iceregistry.cfg" % workingdirectory
        self.iceGridAdminConfigPath = "%s/icegridadmin.cfg" % workingdirectory
        self.iceStormConfigPath = "%s/icestorm.cfg" % workingdirectory
        self.iceRegistryLogPath = "%s/iceregistry.log" % workingdirectory
        self.iceStormLogPath = "%s/icestorm.log" % workingdirectory
        self.iceStormPidPath = "%s/icestorm.pid" % workingdirectory
    
    def start(self):
        logging.info("Trying to start Ice Registry...")

        params = {'registrydatadirectory':'%s/registry' % self.datadirectory,
                  'dbdirectory':'%s/db' % self.datadirectory}
    
        os.mkdir(params['registrydatadirectory'])
        os.mkdir(params['dbdirectory'])
    
        writeIceRegistryConfig(self.iceRegistryConfigPath, params)
        writeIceGridAdminConfig(self.iceGridAdminConfigPath, params)
        writeIceStormConfig(self.iceStormConfigPath, params)
    

        iceRegistryLog = open(self.iceRegistryLogPath, "w")
    
        logging.debug("Ice registry command is 'icegridregistry --Ice.Config=%s'" % self.iceRegistryConfigPath)
        #proc = subprocess.Popen(['icegridregistry', '--Ice.Config=%s' % self.iceRegistryConfigPath], stdout=iceRegistryLog)
        proc = subprocess.Popen(['icegridregistry', '--Ice.Config=%s' % self.iceRegistryConfigPath])
        returncode = proc.poll()
        if returncode != None:
            logging.error("Error: Failed to start ice registry (code %d)" % returncode)
            sys.exit(1)
    
        waitIceRegistry(self.iceGridAdminConfigPath)
    
        logging.info("Trying to start Ice Storm...")
        iceStormLog = open(self.iceStormLogPath, "w")

        logging.debug("Icebox command is 'icebox --Ice.Config=%s'" % self.iceStormConfigPath)
        #proc = subprocess.Popen(['icebox', '--Ice.Config=%s' % self.iceStormConfigPath], stdout=iceStormLog)
        proc = subprocess.Popen(['icebox', '--Ice.Config=%s' % self.iceStormConfigPath])
        returncode = proc.poll()
        if returncode != None:
            logging.error("Error: Failed to start ice storm (code %d)" % returncode)
            sys.exit(1)
    
        with open(self.iceStormPidPath, "w") as iceStormPidFile:
            iceStormPidFile.write('{}'.format(proc.pid))
    
        waitIceStorm(self.iceGridAdminConfigPath)
    
    def stop(self):
        logging.info("Terminating Ice Storm...")
        if os.path.exists(self.iceStormPidPath):
            with open(self.iceStormPidPath, "r") as f:
                pid = int(f.read().strip())
            kill_service(pid)
            os.remove(self.iceStormPidPath)
    
        logging.info("Terminating Ice Registry...")
        try:
            subprocess.check_call(['icegridadmin', '--Ice.Config=%s' % self.iceGridAdminConfigPath, '-u', 'foo', '-p', 'bar', '-e', 'registry shutdown Master'])
        except subprocess.CalledProcessError:
            logging.error("Error stopping registry")
        else:
            logging.info("Ice Storm and Registry terminated.")
    
def signal(pid, sig):
    try:
        os.kill(pid, sig)
    except OSError:
        return False
    else:
        return True
        
def process_exists(pid):
    return signal(pid, 0)
    
def kill(pid):
    return signal(pid, 9)
    
def kill_service(pid):
    if process_exists(pid):
        kill(pid)
        time.sleep(5)
        kill(pid)

def main():
    logging.basicConfig(level=logging.INFO, format='%(threadName)s, %(module)s: %(message)s')

    icerunner = IceRunner("testbed_data")
    icerunner.start()

    time.sleep(15)

    icerunner.stop()

if __name__ == "__main__":
    main()
