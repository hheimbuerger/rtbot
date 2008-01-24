import collections
import re



class TopicQueuePlugin:
  def __init__(self, pluginInterface):
    self.pluginInterfaceReference = pluginInterface
    self.topicQueue = collections.deque()

  def getVersionInformation(self):
    return("$Id: BugReplyPlugin.py 260 2006-05-23 22:37:56Z Ksero $")

  def onChannelMessage(self, irclib, sender, message):
    if(len(message.split()) >= 1):
      command = message.split()[0]

      if((command == "!push") and (len(message.split()) >= 2)):
        topic = message.split(None, 1)[1]
        #reResult = re.compile("\(.*?\)^").search(topic.strip())
        reResult = re.search("\(.*?\)^", topic.strip())
        if(reResult):
          try:
            users = reResult.group(1).split(", ")
            
          except:
            irclib.sendChannelMessage("One or more of the users are invalid.")
        self.topicQueue.append(topic)
        irclib.sendChannelMessage("The topic '%s' has been queued." % (topic))
      elif(command == "!peek"):
        if(len(self.topicQueue) > 0):
          irclib.sendChannelMessage("The next topic is '%s'." % (self.topicQueue[0]))
        else:
          irclib.sendChannelMessage("There are no queued topics.")
      elif(command == "!listtopics"):
        topics
      elif(command == "!pop"):
        if(len(self.topicQueue) > 0):
          irclib.sendChannelMessage("The topic is now '%s'." % (self.topicQueue.popleft()))
        else:
          irclib.sendChannelMessage("There are no queued topics.")





if __name__ == "__main__":
    class PluginInterfaceMock:
        def getPlugin(self, name):
            return(AuthPluginMock())

    class IrcLibMock:
        nickname = "RTBot"
        def sendPrivateMessage(self, target, text):
            print text
        def sendChannelMessage(self, text):
            print text
        def sendChannelEmote(self, text):
            print "* %s" % (text)

    queue = TopicQueuePlugin(PluginInterfaceMock())
    queue.onChannelMessage(IrcLibMock(), "source", "!push abc")
    queue.onChannelMessage(IrcLibMock(), "source", "!push def ghi")
    queue.onChannelMessage(IrcLibMock(), "source", "!peek")
    queue.onChannelMessage(IrcLibMock(), "source", "!pop")
    queue.onChannelMessage(IrcLibMock(), "source", "!pop")
    queue.onChannelMessage(IrcLibMock(), "source", "!peek")
    queue.onChannelMessage(IrcLibMock(), "source", "!pop")
