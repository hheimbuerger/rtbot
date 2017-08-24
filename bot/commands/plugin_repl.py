"""
Usage: Run from base directory in shell, passing in a plugin name as an argument.

Example: python plugin_repl PollPlugin

Takes you into a direct communication with a plugin via stdin/stdout.
"""

import asyncio
import importlib.util
import inspect
import sys

from plugin_base import BasePlugin


class MockClient:
    pass

class MockUser:
    @property
    def id(self):
        return 1

    @property
    def name(self):
        return 'Joe Tester'

    def __str__(self):
        return self.name

class MockChannel:
    async def reply(self, message):
        print(message)


async def simulate_plugin_execution(plugin):
    user = MockUser()
    channel = MockChannel()

    while True:
        message = input('>>> ')
        if message == '%timer':
            await plugin.on_timer()
        else:
            await plugin.on_message(channel, user, message)


def find_all_inheriting_classes_from_module(module, base_class):
    for name, obj in inspect.getmembers(module):
        if inspect.isclass(obj):
            cls = obj
            if issubclass(cls, base_class) and not cls == base_class:
                yield cls


def load_module_by_name(plugin_name):
    spec = importlib.util.spec_from_file_location(plugin_name, 'plugins/'+plugin_name+'.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


if __name__ == '__main__':
    # load module
    module = load_module_by_name(sys.argv[1])

    # instantiate plugin
    plugins = list(find_all_inheriting_classes_from_module(module, BasePlugin))
    assert len(plugins) == 1
    plugin_instance = plugins[0]()

    # simulate plugin execution in event loop
    asyncio.get_event_loop().run_until_complete(simulate_plugin_execution(plugin_instance))
