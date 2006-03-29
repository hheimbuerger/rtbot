import string



class MinerLoadCalculationPlugin:

    def __init__(self):
        self.cores = ["DN", "EoR", "A+", "PC2"]

        self.baseHeliumConstant = {}
        self.baseHeliumConstant["DN"] = 1500.0
        self.baseHeliumConstant["EoR"] = 1500.0
        self.baseHeliumConstant["A+"] = 1500.0
        self.baseHeliumConstant["PC2"] = 1500.0

        self.defaultMinerCapacity = {}
        self.defaultMinerCapacity["DN"] = 90.0
        self.defaultMinerCapacity["EoR"] = 90.0
        self.defaultMinerCapacity["A+"] = 90.0
        self.defaultMinerCapacity["PC2"] = 90.0

        self.mapSectors = {}
        self.mapSectors["star"] = 12
        self.mapSectors["hihigher"] = 13
        self.mapSectors["insideout"] = 13
        self.mapSectors["hilo"] = 9
        self.mapSectors["hilo4for2"] = 17

        self.minerCapacityModifier = {}
        self.minerCapacityModifier["DN"] = []
        self.minerCapacityModifier["DN"].append(("Belters", 0.8))
        self.minerCapacityModifier["DN"].append(("Bios", 1.0))
        self.minerCapacityModifier["DN"].append(("Dreghklar", 0.75))
        self.minerCapacityModifier["DN"].append(("Ga'Taraan", 1.0))
        self.minerCapacityModifier["DN"].append(("Gigacorp", 1.25))
        self.minerCapacityModifier["DN"].append(("Iron Coalition", 0.75))
        self.minerCapacityModifier["DN"].append(("Phoenix", 1.0))
        self.minerCapacityModifier["DN"].append(("Rixian", 1.0))
        self.minerCapacityModifier["DN"].append(("Technoflux", 0.55))
        self.minerCapacityModifier["EoR"] = []
        self.minerCapacityModifier["EoR"].append(("Belters", 0.6))
        self.minerCapacityModifier["EoR"].append(("Bios", 1.0))
        self.minerCapacityModifier["EoR"].append(("Ga'Taraan", 0.8))
        self.minerCapacityModifier["EoR"].append(("Gigacorp", 1.25))
        self.minerCapacityModifier["EoR"].append(("Iron Coalition", 0.85))
        self.minerCapacityModifier["EoR"].append(("Rixian", 1.0))
        self.minerCapacityModifier["A+"] = []
        self.minerCapacityModifier["A+"].append(("Belters", 0.8))
        self.minerCapacityModifier["A+"].append(("Bios", 1.0))
        self.minerCapacityModifier["A+"].append(("Dreghklar", 0.909))
        self.minerCapacityModifier["A+"].append(("Ga'Taraan", 1.0))
        self.minerCapacityModifier["A+"].append(("Gigacorp", 1.25))
        self.minerCapacityModifier["A+"].append(("Iron Coalition", 0.75))
        self.minerCapacityModifier["A+"].append(("Rixian", 1.0))
        self.minerCapacityModifier["PC2"] = []
        self.minerCapacityModifier["PC2"].append(("Belters", 0.8))
        self.minerCapacityModifier["PC2"].append(("Bios", 1.0))
        self.minerCapacityModifier["PC2"].append(("Gigacorp", 1.25))
        self.minerCapacityModifier["PC2"].append(("Iron Coalition", 0.9))

        self.moneySettings = {}
        self.moneySettings["low"] = 0.75
        self.moneySettings["medlow"] = 0.75
        self.moneySettings["med"] = 1.0
        self.moneySettings["medhigh"] = 1.15
        self.moneySettings["high"] = 1.25
        self.moneySettings["higher"] = 1.35
        self.moneySettings["highest"] = 1.5
        self.moneySettings["biggame"] = 2.5

        self.resourceSettings = {}
        self.resourceSettings["veryscarce"] = (0, 2)
        self.resourceSettings["scarce"] = (1, 2)
        self.resourceSettings["normal"] = (2, 4)
        self.resourceSettings["equal"] = (2, 2)
        self.resourceSettings["plentiful"] = (2, 4)

    def getVersionInformation(self):
        return("$Id$")

    def onChannelMessage(self, irclib, source, msg):
        if(len(msg.split()) >= 1):
            if(msg.split()[0] == "minercalc"):
                if(len(msg.split()) >= 5):
                    # determine selected core
                    core = msg.split()[1]
                    if(not (core in self.cores)):
                        irclib.sendChannelMessage("Error: <core> has to be one of these: %s" % (string.join(self.cores, ", ")))
                        return

                    # calculate base miner capacity and base helium
                    defaultMinerCapacity = self.defaultMinerCapacity[core]
                    baseHelium = self.baseHeliumConstant[core]

                    # determine number of sectors
                    mapDefinitionString = string.lower(msg.split()[2])
                    if(mapDefinitionString in self.mapSectors.keys()):
                        sectorCount = self.mapSectors[mapDefinitionString]
                    else:
                        try:
                            sectorCount = int(mapDefinitionString)
                        except ValueError:
                            listOfKnownMaps = self.mapSectors.keys()
                            irclib.sendChannelMessage("Error: <map name / number of sectors> has to be one of these: %s, or a whole number." % (string.join(listOfKnownMaps, ", ")))
                            return
                    
                    # determine money settings
                    moneySettingsString = string.lower(msg.split()[3])
                    if(moneySettingsString in self.moneySettings.keys()):
                        moneyModifier = self.moneySettings[moneySettingsString]
                    else:
                        listOfAllowedMoneySettings = self.moneySettings.keys()
                        irclib.sendChannelMessage("Error: <money setting> has to be one of these: %s" % (string.join(listOfAllowedMoneySettings, ", ")))
                        return

                    # determine resource settings
                    resourceSettingsString = string.lower(msg.split()[4])
                    if(resourceSettingsString in self.resourceSettings.keys()):
                        (rocksPerHomeSectorCount, rocksPerStandardSectorCount) = self.resourceSettings[resourceSettingsString]
                    else:
                        listOfAllowedResourceSettings = self.resourceSettings.keys()
                        irclib.sendChannelMessage("Error: <resource setting> has to be one of these: %s" % (string.join(listOfAllowedResourceSettings, ", ")))
                        return

                    # do the calculations
                    totalHelium = 2*baseHelium * moneyModifier
                    homeSectorCount = 2
                    standardSectorCount = sectorCount - homeSectorCount
                    totalRocks = (homeSectorCount * rocksPerHomeSectorCount) + (standardSectorCount * rocksPerStandardSectorCount)
                    hePerRock = totalHelium / totalRocks

                    # give detailed output if requested
                    if((len(msg.split()) >= 6) and (msg.split()[5] == "/detailed")):
                        irclib.sendChannelMessage("=== Detailed output following: ===")
                        irclib.sendChannelMessage("baseHelium: %i" % baseHelium)
                        irclib.sendChannelMessage("sectorCount: %i" % sectorCount)
                        irclib.sendChannelMessage("rocksPerHomeSectorCount: %i" % rocksPerHomeSectorCount)
                        irclib.sendChannelMessage("rocksPerStandardSectorCount: %i" % rocksPerStandardSectorCount)
                        irclib.sendChannelMessage("totalHelium: %f" % totalHelium)
                        irclib.sendChannelMessage("homeSectorCount: %i" % homeSectorCount)
                        irclib.sendChannelMessage("standardSectorCount: %i" % standardSectorCount)
                        irclib.sendChannelMessage("totalRocks: %i" % totalRocks)
                        irclib.sendChannelMessage("hePerRock: %f" % hePerRock)
                        irclib.sendChannelMessage("=== End of detailed output ===")

                    # give main output
                    output = []
                    for (factionName, factionCapacityModifier) in self.minerCapacityModifier[core]:
                        factionMinerCapacity = defaultMinerCapacity * factionCapacityModifier
                        minerLoadsPerRock = round(hePerRock / factionMinerCapacity, 2)
                        output.append("%s: %s" % (factionName, str(round(minerLoadsPerRock, 2))))
                    irclib.sendChannelMessage("The miner loads per rock are: %s" % (string.join(output, ", ")))
                else:
                    # if no parameter specified: print syntax
                    irclib.sendChannelMessage("Syntax: minercalc <core> <map name / number of sectors> <money setting> <resource setting>")






#Unit-test
if __name__ == "__main__":
    class FakeIrcLib:
        def sendPrivateMessage(self, target, text):
            print text
        def sendChannelMessage(self, text):
            print text

    a = MinerLoadCalculationPlugin()
    a.onChannelMessage(FakeIrcLib(), "source", "minercalc abc 12 med normal")
    print "==============="
    a.onChannelMessage(FakeIrcLib(), "source", "minercalc DN 12 med normal")
    print "==============="
    a.onChannelMessage(FakeIrcLib(), "source", "minercalc DN 12 123 normal")
    print "==============="
    a.onChannelMessage(FakeIrcLib(), "source", "minercalc DN 12 med 123")
    print "==============="
    a.onChannelMessage(FakeIrcLib(), "source", "minercalc DN abc med normal")
    print "==============="
    a.onChannelMessage(FakeIrcLib(), "source", "minercalc DN HiLo med normal /detailed")
