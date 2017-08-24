from plugins.PollPlugin import PollPlugin
from tests.utils import PluginTestCase


class PollPluginTest(PluginTestCase):
    def __init__(self, methodName='runTest'):
        self.plugin = PollPlugin()
        super(PollPluginTest, self).__init__(methodName, self.plugin)

    def test_basic_behavior(self):
        response = self.simulate_message('!poll "Question?" "Yes" "No" 15')
        self.assertTrue('Poll: Question?' in response)
        self.assertIn('#1: "Yes"', response)
        self.assertIn('#2: "No"', response)
        self.assertSingleLineResponse('!vote 1', 'Your vote has been counted, Joe Tester.')
        self.assertSingleLineResponse('!vote 2', 'Your vote has been changed, Joe Tester.')
        self.assertSingleLineResponse('!vote 3', 'That vote-id is invalid, Joe Tester.')
        # TODO: test post-timeout behavior
