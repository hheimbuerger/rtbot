import csv
import datetime
from modules import PluginInterface
from modules import LogLib

class MailboxPlugin:

    storedMails = []

    def __init__(self, pluginInterface):
        self.pluginInterfaceReference = pluginInterface
        self.loadMails()
        
    def getVersionInformation(self):
        return("$Id$")

    @classmethod
    def getDependencies(self):
        return(["AuthenticationPlugin"])

    def loadMails(self):
      self.storedMails = []
      file = open("resources/mails.csv", "rb")
      reader = csv.reader(file)
      for row in reader:
        self.storedMails.append(row)
      file.close()

    def saveMails(self):
      writer = csv.writer(open("resources/mails.csv", "wb"))
      writer.writerows(self.storedMails)

    def isFriend(self, irclib, name):
        # retrieve AuthenticationPlugin
        authenticationPlugin = self.pluginInterfaceReference.getPluginByClassname("AuthenticationPlugin")
        if(authenticationPlugin == None):
          LogLib.log.add(LogLib.LOGLVL_INFO, "ERROR: MailboxPlugin didn't succeed at lookup of AuthenticationPlugin during execution of isFriend()")
          return(None)
        else:
          return(authenticationPlugin.isFriend(irclib, name))

    def isKnown(self, username):
        # retrieve AuthenticationPlugin
        authenticationPlugin = self.pluginInterfaceReference.getPluginByClassname("AuthenticationPlugin")
        if(authenticationPlugin == None):
          LogLib.log.add(LogLib.LOGLVL_INFO, "ERROR: MailboxPlugin didn't succeed at lookup of AuthenticationPlugin during execution of isKnown()")
          return(None)
        else:
          return(authenticationPlugin.isKnown(username))

    def getCanonicalName(self, rawName):
      # retrieve AuthenticationPlugin
      authenticationPlugin = self.pluginInterfaceReference.getPluginByClassname("AuthenticationPlugin")
      if(authenticationPlugin == None):
        LogLib.log.add(LogLib.LOGLVL_INFO, "ERROR: MailboxPlugin didn't succeed at lookup of AuthenticationPlugin during execution of getCanonicalName()")
        return(rawName)
      else:
        return(authenticationPlugin.getCanonicalName(rawName))

    def sendMessage(self, sender, receiver, message, needDeliveryNotification, isDeliveryNotification, instantDelivery = False):
        time = datetime.datetime.utcnow().strftime("%d.%m.%Y %H:%M:%S")
        self.storedMails.append((self.getCanonicalName(sender), self.getCanonicalName(receiver), message, time, needDeliveryNotification, isDeliveryNotification))
        self.saveMails()

    def sendDeliveryNotification(self, irclib, sender, receiver, message, date):
        deliveryMessage = "Your message '%s' from %s to %s has been delivered." % (message, date, receiver)

        # try to deliver the delivery notification right away
        userList = irclib.getUserList().getDictionaryWithFlags()
        for user in userList.keys():
            if(self.getCanonicalName(user) == sender):
                irclib.sendPrivateMessage(user, deliveryMessage)
                return

        # not possible? Then send it as a message...
        self.sendMessage("RTBot", sender, deliveryMessage, False, True)

    def retrieveMessage(self, irclib, person, authedName = None):
        for mail in self.storedMails:
            (sender, receiver, message, date, needDeliveryNotification, isDeliveryNotification) = mail
            if((receiver == person) or (authedName and receiver == '@'+authedName)):
                LogLib.log.add(LogLib.LOGLVL_DEBUG, "Deleting message that is about to be delivered: |%s|" % (str(mail)))
                self.storedMails.remove(mail)
                self.saveMails()
                if(needDeliveryNotification):
                    self.sendDeliveryNotification(irclib, sender, receiver, message, date)
                return((sender, message, date, isDeliveryNotification))
        return(None)

    def deliverMessages(self, irclib, receiver):
        authedName = self.isFriend(irclib, receiver)
        while(True):
            mail = self.retrieveMessage(irclib, self.getCanonicalName(receiver), authedName)
            if(mail == None):
                return
            else:
                (sender, message, date, isDeliveryNotification) = mail
                if(isDeliveryNotification):
                    irclib.sendPrivateMessage(receiver, message)
                else:
                    irclib.sendPrivateMessage(receiver, "%s told me on %s to give you this message: '%s'" % (sender, date, message))
                    irclib.sendPrivateMessage(receiver, "If you want to reply and the person is not around, tell me \"message %s <message>\". I will ignore any AFK-tags." % (sender))

    def displayOutbox(self, irclib, source):
        outgoingMails = []
        canonicalSource = self.getCanonicalName(source)
        for mail in self.storedMails:
            (sender, receiver, message, date, needDeliveryNotification, isDeliveryNotification) = mail
            if(sender == canonicalSource):
                outgoingMails.append("%s hasn't yet fetched the message '%s' from %s" % (receiver, message, date))
        if(len(outgoingMails) == 0):
            irclib.sendPrivateMessage(source, "You haven't sent any messages that haven't been received yet.")
        else:
            for mail in outgoingMails:
                irclib.sendPrivateMessage(source, mail)

    def onJoin(self, irclib, source):
        self.deliverMessages(irclib, source)

    def onChangeNick(self, irclib, source, target):
        self.deliverMessages(irclib, target)

    def onPrivateMessage(self, irclib, source, msg):
        if((len(msg.split()) > 2) and (msg.split()[0] == "message")):
            receiver = msg.split()[1]
            message = msg.split(None, 2)[2]
            if(message[-8:] == " /notify"):
                wantDeliveryNotification = True
                message = message[:-8]
            else:
                wantDeliveryNotification = False
            if(receiver[0] == '@' and not self.isKnown(receiver[1:])):
                irclib.sendPrivateMessage(source, "Sorry, %s isn't one of my friends." % (receiver[1:]))
                return
            self.sendMessage(self.getCanonicalName(source), receiver, message, wantDeliveryNotification, False)
            if(wantDeliveryNotification):
                irclib.sendPrivateMessage(source, "Ok, I will tell %s this message and notify you when it is delivered: %s" % (receiver, message))
            else:
                irclib.sendPrivateMessage(source, "Ok, I will tell %s this message: %s" % (receiver, message))
            return(True)
        elif(msg == "outbox"):
            self.displayOutbox(irclib, source)
            return(True)





if __name__ == "__main__":
    mailbox = MailboxPlugin(None)
    mailbox.sendMessage("me", "you", "Hello, \"world\"!")
    print mailbox.retrieveMessage("nobody")
    print mailbox.retrieveMessage("you")
