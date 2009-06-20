# These imports are only used for the unit-test code, they are ignored when used as a plugin (but all of them are automatically imported by the PluginInterface)
import re, os



class CoreReaderPlugin:

    import plugins.CoreReaderPlugin.igc

    def getVersionInformation(self):
        return("$Id$")

    def __init__(self):
        pass

    def readCore(self, core):
        reader = self.plugins.CoreReaderPlugin.igc.IGCReader()
        try:
            reader.open("resources/cores/" + core + ".igc")
            return(reader)
        except IOError:
            return(None)

    def getObjectAttributes(self, core, objectlist, namekey, searchterm):
        # create the search RE
        expression = "(.*?)"
        for word in searchterm.split():
            expression += re.escape(word) + "(.*?)"

        for object in objectlist: 
            if re.match(expression, object.attribs[namekey].lower()):
                result = {}
                for attrib in object.attribs.keys():
                    result[attrib] = str(object.attribs[attrib])
                return(result)

        return([])

    def getFormattedOutput(self, attriblist, namekey, displayattribs):
        result = []
        result.append(attriblist[namekey] + ":")
        for attrib in displayattribs:
            result.append(attrib + " = " + attriblist[attrib])
        return(result)

    def getObjectAttributesString(self, core, objectlist, namekey, searchterm):
        # create the search RE
        expression = "(.*?)"
        for word in searchterm.split():
            expression += re.escape(word) + "(.*?)"

        for object in objectlist: 
            if re.match(expression, object.attribs[namekey].lower()):
                result = []
                for attrib in object.attribs.keys():
                    #filter unintersting details
                    if ("sound" not in attrib) and (attrib != "description") and (not "_id" in attrib) and \
                       ("_mask" not in attrib) and ("next_" not in attrib) and (attrib != "loadout") and \
                       (attrib != namekey) and (attrib != "pre") and (attrib != "def") and (attrib != "locals"):
                            #attempt to pretty print
                            value = object.attribs[attrib]
                            if(type(value) == float):
                                value = "%.1f" % value
                            result.append(attrib + " = " + str(value))
                return(object.attribs[namekey] + ": " + "; ".join(result))

        return("Couldn't find object!")

    def onChannelMessage(self, irclib, source, msg):
        if((len(msg.split()) >= 4) and (msg.split()[0] == "core")):
            (basecommand, core, command, arguments) = msg.split(None, 3)

            # read the core
            reader = self.readCore(core)
            if(not reader):
                irclib.sendChannelMessage("Couldn't find core!")
                return

            if(command.lower() == "ship"):
                irclib.sendChannelMessage(self.getObjectAttributesString(core, reader.ships, "name", arguments))
            elif(command.lower() == "faction"):
                irclib.sendChannelMessage(self.getObjectAttributesString(core, reader.factions, "name", arguments))
            elif(command.lower() == "weapon"):
                irclib.sendChannelMessage(self.getObjectAttributesString(core, reader.weapons, "name", arguments))
            elif(command.lower() == "shield"):
                irclib.sendChannelMessage(self.getObjectAttributesString(core, reader.shields, "name", arguments))
            elif(command.lower() == "cloak"):
                irclib.sendChannelMessage(self.getObjectAttributesString(core, reader.cloaks, "name", arguments))
            elif(command.lower() == "missile"):
                irclib.sendChannelMessage(self.getObjectAttributesString(core, reader.missiles, "ld_name", arguments))
            elif(command.lower() == "mine"):
                irclib.sendChannelMessage(self.getObjectAttributesString(core, reader.mines, "ld_name", arguments))
            elif(command.lower() == "probe"):
                irclib.sendChannelMessage(self.getObjectAttributesString(core, reader.probes, "ld_name", arguments))
            elif(command.lower() == "projectile"):
                irclib.sendChannelMessage(self.getObjectAttributesString(core, reader.projectiles, "name", arguments))
            elif(command.lower() == "station"):
                irclib.sendChannelMessage(self.getObjectAttributesString(core, reader.stations, "name", arguments))
            elif(command.lower() == "chaff"):
                irclib.sendChannelMessage(self.getObjectAttributesString(core, reader.chaff, "ld_name", arguments))
            elif(command.lower() == "tech"):
                irclib.sendChannelMessage(self.getObjectAttributesString(core, reader.techs, "name", arguments))
            elif(command.lower() == "booster"):
                irclib.sendChannelMessage(self.getObjectAttributesString(core, reader.boosters, "name", arguments))

        elif msg == "core list":
            files = [corefile.replace(".igc", "") for corefile in os.listdir("resources/cores/")
                     if ".igc" in corefile]
            files = " ".join(files)
            irclib.sendChannelMessage("Available cores are: " + files)
            
        



if __name__ == "__main__":
    import sys
    import string

    class FakeIrcLib:
        def sendPrivateMessage(self, target, text):
            print text
        def sendChannelMessage(self, text):
            print text

    corelib = CoreReaderPlugin()
    corelib.onChannelMessage(FakeIrcLib(), "source", "core dn_000405 " + "".join(sys.argv[1:]))
