class BasePlugin:
    async def send_message(self, destination, message):
        """
        Sends the given message to the specified destination (user or channel).

        :param destination: can be a `User` object or a `Channel` object
        :param message: the `str` message to send (may contain line breaks)
        """
        await self.plugin_context.dispatch_message(destination, message)
