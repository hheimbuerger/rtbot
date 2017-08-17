import asyncio
import unittest


class MessageContextMock:
    def __init__(self):
        self.response_buffer = []

    async def reply(self, message):
        self.response_buffer.append(message)


class PluginTestCase(unittest.TestCase):
    def __init__(self, methodName, plugin):
        self.plugin = plugin
        super(PluginTestCase, self).__init__(methodName)

    def simulate_message(self, message):
        ctx = MessageContextMock()
        from core.client import User
        coro = self.plugin.on_message(ctx, User('foo'), message)
        asyncio.get_event_loop().run_until_complete(coro)
        return ctx.response_buffer

    def assertSingleLineResponse(self, command, expected_response):
        """
        Asserts that when sending the command `command` to the bot, she will respond with a single line containing
        `expected_response`.
        """
        actual_response = self.simulate_message(command)
        self.assertEqual(len(actual_response), 1)
        self.assertEqual(actual_response[0], expected_response)
