# -*- coding: iso-8859-15 -*-

import re
import string
import httplib
import xml.dom.minidom



class CurrencyPlugin:

    def __init__(self):
        self.currencyTableSource = {"host": "www.ecb.int", "url": "/stats/eurofxref/eurofxref-daily.xml"}
        self.usedCurrencies = ["EUR", "GBP", "USD", "CAD", "SKK", "SEK", "NZD", "INR", "NIS"]          # removed: "AUD", "DKK"
        self.currencyRE = " (\\d{1,10}(\\.\\d{2})?)"
        self.fixedCurrencies = {"INR": 55.7700, "NIS": 5.8637}
        self.fixedCurrencyUpdate = "2007/08/09"

    def getVersionInformation(self):
        return("$Id$")

    def getCurrencyTable(self):
        (status, document, location) = self.getPage(self.currencyTableSource["host"], self.currencyTableSource["url"])
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
        # iterate over all used currencies
        for currency in self.usedCurrencies:
            # check if this currency is used in the message
            RE = currency + self.currencyRE
            result = re.search(RE, string.upper(message))
            if(result):
                currencyTable = self.getCurrencyTable()

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


(lambda reply: irclib.sendChannelMessage(reply))

if __name__ == "__main__":
    class FakeIrcLib:
        def sendPrivateMessage(self, target, text):
            print text
        def sendChannelMessage(self, text):
            print text
    
    a = CurrencyPlugin()
#    a.getCurrencyTable()
    a.onChannelMessage(FakeIrcLib(), "source", "USD 10")
    a.onChannelMessage(FakeIrcLib(), "source", "SKK 123.38")
    a.onChannelMessage(FakeIrcLib(), "source", "EUR 10, USD 20")
    a.onChannelMessage(FakeIrcLib(), "source", "INR 40.4000")
