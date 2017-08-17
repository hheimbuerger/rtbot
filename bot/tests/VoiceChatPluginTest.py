from plugins.VoiceChatPlugin import VoiceChatPlugin
from tests.utils import PluginTestCase


class VoiceChatPluginTest(PluginTestCase):
    def __init__(self, methodName='runTest'):
        self.plugin = VoiceChatPlugin()
        super(VoiceChatPluginTest, self).__init__(methodName, self.plugin)

    def test_pass(self):
        self.assertSingleLineResponse('findvc default fir', "default: '1 = Affirmative")
        self.assertSingleLineResponse("findvc CortDialect heh heh", 'INSERT EXPECTED RESPONSE HERE')
        self.assertSingleLineResponse("vc default ~ra", 'INSERT EXPECTED RESPONSE HERE')
        self.assertSingleLineResponse("vc '1", 'INSERT EXPECTED RESPONSE HERE')
        self.assertSingleLineResponse("findvc affir", 'INSERT EXPECTED RESPONSE HERE')
        self.assertSingleLineResponse("vcpref TigereyeDialect", 'INSERT EXPECTED RESPONSE HERE')
        self.assertSingleLineResponse("vc `tqa", 'INSERT EXPECTED RESPONSE HERE')  # Should be "Out of ammo - interesting"
        self.assertSingleLineResponse("vcpref Nonexistant", 'INSERT EXPECTED RESPONSE HERE')
