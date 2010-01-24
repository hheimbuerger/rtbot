# -*- coding: iso-8859-15 -*-

import re
import string
import datetime
import types
import httplib
import xml.dom.minidom



class UnitConversionPlugin:

    def __init__(self):
        self.currencyTableSource = {"host": "www.ecb.int", "url": "/stats/eurofxref/eurofxref-daily.xml"}
        self.usedCurrencies = ["EUR", "GBP", "USD", "CAD", "NZD", "PLN", "INR", "NIS"]          # removed: "AUD", "DKK", "SKK", "SEK", "NOK",
        self.currencyRE = "\s?(\\d{1,10}(\\.\\d{2})?)"
        self.fixedCurrencies = {"INR": 65.301296, "NIS": 5.54656082}
        self.fixedCurrencyUpdate = "2009-05-21"
        self.lastCurrencyUpdate = None
        self.lastCurrencyTable = None
        
        #self.temperatureRE = "([-+]\\d{1,3}(\\.\\d)?)([KCF])"
        
        # The conversion table has the following format:
        # It's a tuple of
        #     tuples of
        #         an RE to detect whether this conversion is appropriate on the given line, and whose first group can be converted to a float and defines the input value
        #         and a list of
        #              tuples of
        #                  a factor or lambda to calculate the conversion
        #                  and an output mask (these will later be concatinated with equal signs) whose first placeholder is a floating value for the result
        self.openConversionTable = (("(?P<value>\\d{1,6}(\\.\\d{1,2})?)((mpg)|(\\smiles per gallon))", [(1.0, "%.02f miles per gallon"), (lambda value: 1.0/value*235.214583, "%.02f litres per 100 kilometres"), (0.425143707, "%.02f kilometres per litre")]),
                                    ("(?P<value>\\d{1,6}(\\.\\d{1,2})?)((lpk)|(\\slit((re)|(er))s? per 100 kilomet((re)|(er))s?))", [(1.0, "%.02f litres per 100 kilometres"), (lambda value: 1.0/value*235.214583, "%.02f miles per gallon"), (lambda value: 100/value, "%.02f kilometres per litre")]),
                                    ("(?P<value>\\d{1,6}(\\.\\d{1,2})?)((kpl)|(\\skilomet((re)|(er))s? per lit((re)|(er))s?))", [(1.0, "%.02f kilometres per litre"), (lambda value: 100/value, "%.02f litres per 100 kilometres"), (2.35214583, "%.02f miles per gallon")]),

                                    ("(?P<value>\\d{1,6}(\\.\\d{1,2})?)((yd)|(\\syards?))", [(1.0, "%.02fyd"), (0.9144, "%.02fm")]),
                                    ("(?P<value>\\d{1,6}(\\.\\d{1,2})?)((ft)|(\\sfeet)|(\\sfoot))", [(1.0, "%.02fft"), (0.3048, "%.02fm")]),
                                    ("(?P<value>\\d{1,6}(\\.\\d{1,2})?)((in)|(\\sinch(es)?))", [(1.0, "%.02fin"), (2.54, "%.02fcm")]),
                                    ("(?P<value>\\d{1,6}(\\.\\d{1,2})?)((m)|(\\smeters?))", [(1.0, "%.02fm"), (1.0936, "%.02fyd")]),             #, (3.2808, "%.01fft")
                                    ("(?P<value>\\d{1,6}(\\.\\d{1,2})?)((cm)|(\\scentimeters))", [(1.0, "%.02fcm"), (0.3937, "%.02fin")]),
                                    ("(?P<value>\\d{1,6}(\\.\\d{1,2})?)((mi)|(\\smiles))", [(1.0, "%.02f miles"), (1.6093, "%.02fkm")]),
                                    ("(?P<value>\\d{1,6}(\\.\\d{1,2})?)((km)|(\\skilometers))", [(1.0, "%.02fkm"), (0.621, "%.02f miles")]),
                                    ("(?P<value>\\d{1,6}(\\.\\d{1,2})?)((mph)|(mi/h))", [(1.0, "%.02fmph"), (1.609344, "%.02fkph"), (0.44704, "%.02fm/s")]),
                                    ("(?P<value>\\d{1,6}(\\.\\d{1,2})?)((kph)|(km/h))", [(1.0, "%.02fkph"), (0.62137, "%.02fmph"), (0.27778, "%.02fm/s")]),
                                    ("(?P<value>\\d{1,6}(\\.\\d{1,2})?)((lbs?)|(\\spounds))", [(1.0, "%.02flb"), (0.45359237, "%.02fkg")]),
                                    ("(?P<value>\\d{1,6}(\\.\\d{1,2})?)((kg)|(\\skilograms))", [(1.0, "%.02fkg"), (2.20462262, "%.02flb")]),

                                    (r"(?P<value>[-+]?\d{1,4}(\.\d)?)\s?((°)|(degrees?\s))?C(elsius)?", [(1.0, "%.01f°C"), ((lambda value: (value*1.8)+32), "%.01f°F")]),
									# old: "(?P<value>[-+]?\\d{1,4}(\\.\\d)?)°?F(ahrenheit)?"
                                    (r"(?P<value>[-+]?\d{1,4}(\.\d)?)\s?((°)|(degrees?\s))?F(ahrenheit)?", [(1.0, "%.01f°F"), ((lambda value: (value-32)/1.8), "%.01f°C")]),
                                    (r"(?P<value>[-+]?\d{1,4}(\.\d)?)\s?((°)|(degrees?\s))?K(elvin)?", [(1.0, "%.01f°K"), ((lambda value: value-273.15), "%.01f°C"), ((lambda value: (value*1.8)-459.67), "%.01f°F")]),

                                    ("(?P<value>\\d{1,6}(\\.\\d{1,2})?)((g)|(gal)|(\\sgallons?))", [(1.0, "%.02fgal"), (3.78496, "%.02fl")]),
                                    ("(?P<value>\\d{1,6}(\\.\\d{1,2})?)((l)|(\\slitres?)|(\\sliters?))", [(1.0, "%.02fl"), (1.0/3.78496, "%.02fgal")]),
                                   )


    def getVersionInformation(self):
        return("$Id$")

    def retrieveCurrencyTable(self, irclib):
        # retrieve the information from the ECB
        startTime = datetime.datetime.utcnow()
        (status, document, location) = self.getPage(self.currencyTableSource["host"], self.currencyTableSource["url"])
        endTime = datetime.datetime.utcnow()
        elapsedTime = endTime-startTime
        if(elapsedTime.seconds > 10):
            irclib.sendChannelEmote("noticed that took %i.%i seconds -- does the ECB not like me, or what!?" % (elapsedTime.seconds, elapsedTime.microseconds/100000))
        else:
            irclib.sendChannelEmote("noticed that took %i.%i seconds." % (elapsedTime.seconds, elapsedTime.microseconds/100000))
                
        # parse the information
        dom = xml.dom.minidom.parseString(document)
        envelope = dom.getElementsByTagName("gesmes:Envelope")[0]
        cubelist = envelope.getElementsByTagName("Cube")[0]
        cube = cubelist.getElementsByTagName("Cube")[0]
        cubes = cube.getElementsByTagName("Cube")
        currencyTable = {}
        currencyTable["EUR"] = 1.00
        for currency in cubes:
            currencyTable[currency.getAttribute("currency")] = float(currency.getAttribute("rate"))
        for (currency, amountPer1EUR) in self.fixedCurrencies.items():
            currencyTable[currency] = float(amountPer1EUR)
        return(currencyTable)

    def getCurrencyTable(self, irclib):
        if(  # if we don't have a currency table yet or if there is no update date,
             (not self.lastCurrencyTable or not self.lastCurrencyUpdate)
             # or if the last currency table update has been yesterday and it's after 14UTC (educated guess that this will always be after the daily update at "2.15 p.m. (14:15) ECB time")
             or (self.lastCurrencyUpdate < datetime.date.today() and datetime.datetime.utcnow().hour >= 14)):
            # then we'll update now
            irclib.sendChannelEmote("retrieves new currency table from the ECB (this may take up to 30 seconds).")
            self.lastCurrencyTable = self.retrieveCurrencyTable(irclib)
            self.lastCurrencyUpdate = datetime.date.today()
        return(self.lastCurrencyTable)

    def getPage(self, host, url):
        conn = httplib.HTTPConnection(host)
        conn.request("GET", url)
        r1 = conn.getresponse()
        #print r1.status, r1.reason, r1.getheader("Location")
        data = r1.read()
        conn.close()
        #LogLib.log.add(False, str((r1.status, data, r1.getheader("Location"))))
        return((r1.status, data, r1.getheader("Location")))

    def onChannelMessage(self, irclib, source, message):
        # check if there are temperatures to be converted
        #result = re.search(self.temperatureRE, message)
        #if(result):
        #    value = float(result.group(1))
        #    if(result.group(3) == "C" and value >= -273.15):
        #        irclib.sendChannelMessage("%.01f°C = %.01f°F" % (value, (value*1.8)+32))
        #    elif(result.group(3) == "F" and value >= -459.67):
        #        irclib.sendChannelMessage("%.01f°F = %.01f°C" % (value, (value-32)/1.8))
        #    elif(result.group(3) == "K" and value >= 0.0):
        #        irclib.sendChannelMessage("%.01f°K = %.01f°C = %s°F" % (value, value-273.15, (value*1.8)-459.67))
        
        # various other conversions
        reducedMessage = message
        for (detectionRE, conversionList) in self.openConversionTable:
            # we need to make some adjustments to the RE:
            # 1. it has to be at the beginning of a line or after a space
            # 2. it needs to be followed by the end of the line or a non-alphanumeric character
            finalDetectionRE = "(^|\\s)" + detectionRE + "($|\\W)"

            for result in re.finditer(finalDetectionRE, reducedMessage):
                outputParts = []
                value = float(result.group("value"))
                for (conversion, outputMask) in conversionList:
                    if(isinstance(conversion, types.FloatType)):
                        resultingValue = value * conversion
                    elif(isinstance(conversion, types.LambdaType)):
                        resultingValue = conversion(value)
                    outputParts.append(outputMask % resultingValue)
                irclib.sendChannelMessage(" = ".join(outputParts))
                # now remove the value from our copy of the message string, so it's not resolved again (only happens if there are overlapping rules)
                reducedMessage = reducedMessage.replace(result.group(0), "")

        # iterate over all used currencies
        for currency in self.usedCurrencies:
            # check if this currency is used in the message
            RE = currency + self.currencyRE
            results = re.finditer(RE, string.upper(message))
            for result in results:
                currencyTable = self.getCurrencyTable(irclib)

                # calculate the base value (EUR amount)
                sourceValue = float(result.group(1))
                baseValue = sourceValue / currencyTable[currency]

                # give the output
                output = []
                # set base currency as first value
                if(currency in self.fixedCurrencies.keys()):
                    type = "~"
                else:
                    type = ""
                output.append("%s%s %.2f" % (type, currency, round(baseValue*currencyTable[currency], 2)))
                # append all other currencies but the base currency
                for outputCurrency in self.usedCurrencies:
                    if(outputCurrency != currency):
                        if(outputCurrency in self.fixedCurrencies.keys()):
                            type = "~"
                        else:
                            type = ""
                        output.append("%s%s %.2f" % (type, outputCurrency, round(baseValue*currencyTable[outputCurrency], 2)))
                irclib.sendChannelMessage("%s [last fixed currency update: %s]" % (string.join(output, " = "), self.fixedCurrencyUpdate))



if __name__ == "__main__":
    class FakeIrcLib:
        def sendPrivateMessage(self, target, text):
            print text
        def sendChannelMessage(self, text):
            print text
        def sendChannelEmote(self, text):
            print "/me "+text
    
    a = UnitConversionPlugin()
    a.onChannelMessage(FakeIrcLib(), "source", "USD 10")
    a.onChannelMessage(FakeIrcLib(), "source", "SKK 123.38")
    a.onChannelMessage(FakeIrcLib(), "source", "EUR 10, USD 20")
    a.onChannelMessage(FakeIrcLib(), "source", "INR 40.4000")
    a.onChannelMessage(FakeIrcLib(), "source", "NIS3")
    a.onChannelMessage(FakeIrcLib(), "source", "-10.5C")
    a.onChannelMessage(FakeIrcLib(), "source", "+110F")
    a.onChannelMessage(FakeIrcLib(), "source", "+0K")
    a.onChannelMessage(FakeIrcLib(), "source", "1ft")
    a.onChannelMessage(FakeIrcLib(), "source", "100000m")
    a.onChannelMessage(FakeIrcLib(), "source", "80 miles")
    a.onChannelMessage(FakeIrcLib(), "source", "450km")
    a.onChannelMessage(FakeIrcLib(), "source", "400yd")
    a.onChannelMessage(FakeIrcLib(), "source", "50mph")
    a.onChannelMessage(FakeIrcLib(), "source", "100kph")
    a.onChannelMessage(FakeIrcLib(), "source", "100 pounds")
    a.onChannelMessage(FakeIrcLib(), "source", "100 miles, 50 miles")
    a.onChannelMessage(FakeIrcLib(), "source", " vis(16.1 kilometers) uv(0 out of 16)")
    a.onChannelMessage(FakeIrcLib(), "source", "EUR 10, EUR 20")
    a.onChannelMessage(FakeIrcLib(), "source", "1 miles per gallon")
