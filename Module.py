from core import Daemon
from core import Log
from core import ModuleManager

from circuits import Component
import json
import os
import shutil
import subprocess

class Module(Component):
    __configs = []

    def add_config(self, **options):
        self.__configs.append(options)
        
    def choice_config(self):
        if len(self.__configs) == 1:
            return self.__configs[0]

        if not len(self.__configs):
            Log.error('Not config file')
            return {}

        print('')

        while True:
            for id, config in enumerate(self.__configs):
                print('    %d) %s: %s' % 
                    (id+1, config['name'], config['description']))

            id = int(input('Your choice ID? '))

            if id and id > 0 and id <= len(self.__configs):
                return self.__configs[id-1]

            print('Incorrect choice ID')

    def install_git_module(self, url):
        module_name = url.split('/')[-1].split('-')[1]
        return self.install_module_dependencies(subprocess.getoutput(
            'git clone "%s" "%s%s"' % (url,Daemon.MODULES_PATH, module_name)
        ).split('\n')[0].split()[-1].replace('.', '').replace("'", ''))

    def install_module(self, name):
        Log.debug('install %s module' % name)

        if name.startswith('git:'):
            return self.install_git_module(name[4:])

        return self.install_mola_module(name)

    def install_module_dependencies(self, name):
        return True

    def install_modules(self, config):
        installed = [self.install_module(name) 
            for name in config['modules_require']]
        Log.debug('%d modules installed' % sum(installed))
        return len(config['modules_require']) == sum(installed)
    
    def install_mola_module(self, name):
        # TODO
        return self.install_module_dependencies(name)

    def load_configuration(self):
        conf_path = '%s/config/' % os.path.dirname(os.path.abspath(__file__))
        liste = os.listdir(conf_path)
        loaded = [self.read_config_file(conf_path + name) for name in liste]
        Log.debug('%d install config load' % sum(loaded))

    def read_config_file(self, path):
        if not os.path.isfile(path):
            return False

        with open(path) as config_file:
            self.add_config(**json.load(config_file))
            return True

        Log.error('config file "%s" not found' % path)
        return False

    def started(self, component):
        self.load_configuration()
        config = self.choice_config()
        if not config:
            return

        self.install_modules(config)
        Log.debug('install sucessfull')
        shutil.rmtree('%sinstall' % Daemon.MODULES_PATH)
        Daemon.restart()

