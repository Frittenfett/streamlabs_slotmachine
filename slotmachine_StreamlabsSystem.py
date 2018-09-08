# ---------------------------------------
#   Import Libraries
# ---------------------------------------
import json
import codecs
import os
import clr
import time

clr.AddReference("IronPython.Modules.dll")
import urllib

# ---------------------------------------
#   [Required]  Script Information
# ---------------------------------------
ScriptName = "Slotmachine"
Website = "https://www.twitch.tv/frittenfettsenpai"
Description = "Slotmachine Tool for your slotmachine hardware."
Creator = "frittenfettsenpai"
Version = "1.0.2"


# ---------------------------------------
#   [Required] Intialize Data (Only called on Load)
# ---------------------------------------
def Init():
    global settings, jackpotAmount, lastRound, globalCoolDown
    settingsfile = os.path.join(os.path.dirname(__file__), "settings.json")

    try:
        with codecs.open(settingsfile, encoding="utf-8-sig", mode="r") as f:
            settings = json.load(f, encoding="utf-8")
    except:
        settings = {
            "command": "!slotmachine",
            "commandGive": "!giveSlot",
            "commandReset": "!resetSlot",
            "commandEnableCooldown": "!enableSlotCD",
            "commandDisableCooldown": "!disableSlotCD",
            "enableCooldownOnStartup": 1,
            "cooldown": 1800,
            "minimumRounds": 1,
            "maximumRounds": 5,
            "costPerRound": 1000,
            "startJackpot": 10000,
            "provision": 25,
            "jackpotFileName": "jackpot.txt",
            "slotmachineSound": "",
            "slotmachineSoundVolume": 1.00,
            "languageErrorRoundLmit": "Error! The rounds has to be between {0} and {1}!",
            "languageErrorNotEnoughMoney": "You need at least {0} {1} for this command!",
            "languageErrorCooldown": "Slotmachine is still in cooldown. Try again in {0} seconds!",
            "languageWrongSyntaxOfGiveCommand": "Wrong Syntax! Please use !commandGive <username> <amount>",
            "languageJackpotTime": "{0} want to spin the slotmachine {1} times for {2} {3}. Jackpot is now {4}!",
            "languageWinning": "{0} just won {1} {2}! PogChamp",
            "languageJackpotRefill": "Jackpot was empty and is now refilled with {0} {1}.",
            "languageEnableCooldown": "Global cooldown for Slotmachine is enabled. Now you need to wait each {0} seconds each try.",
            "languageDisableCooldown": "Global cooldown for Slotmachine is disabled. Type {0} as much as you want."
        }

    jackpotFile = os.path.join(os.path.dirname(__file__), settings['jackpotFileName'])
    if os.path.isfile(jackpotFile):
        file = open(jackpotFile, "r")
        jackpotAmount = int(file.read())
        file.close()
    else:
        jackpotAmount = settings["startJackpot"]
        SetJackpot(jackpotAmount)
    lastRound = 0
    globalCoolDown = int(settings["enableCooldownOnStartup"])
    return


# ---------------------------------------
#   [Required] Execute Data / Process Messages
# ---------------------------------------
def Execute(data):
    global settings, jackpotAmount, lastRound, globalCoolDown
    if data.IsChatMessage():
        user = data.User
        username = Parent.GetDisplayName(user)

        if (data.GetParam(0).lower() == settings["command"]):

            rounds = settings["minimumRounds"]
            if data.GetParamCount() > 1:
                rounds = int(data.GetParam(1))
            if rounds < settings["minimumRounds"] or rounds > settings["maximumRounds"]:
                Parent.SendTwitchWhisper(user, settings["languageErrorRoundLmit"].format(settings["minimumRounds"],
                                                                                         settings["maximumRounds"]))
                return

            price = rounds * settings["costPerRound"]
            if (Parent.GetPoints(user) > price):
                timeDiff = time.time() - lastRound
                if globalCoolDown and timeDiff < settings["cooldown"]:
                    Parent.SendTwitchMessage(settings["languageErrorCooldown"].format(int(settings["cooldown"] - timeDiff)))
                    return
                Parent.RemovePoints(user, price)
                jackpotPrice = price
                if settings["provision"] > 0:
                    jackpotPrice = price - int(round(price / 100 * settings["provision"]))
                jackpotAmount = jackpotAmount + jackpotPrice
                Parent.SendTwitchMessage(
                    settings["languageJackpotTime"].format(username, rounds, price, Parent.GetCurrencyName(), jackpotAmount))
                SetJackpot(jackpotAmount)
                lastRound = time.time()
                if (settings['slotmachineSound'] != ""):
                    soundfile = os.path.join(os.path.dirname(__file__), settings['slotmachineSound'])
                    Parent.PlaySound(soundfile, settings['slotmachineSoundVolume'])
            else:
                Parent.SendTwitchWhisper(user, settings["languageErrorNotEnoughMoney"].format(price, Parent.GetCurrencyName()))
        elif (data.GetParam(0) == settings["commandGive"] and Parent.HasPermission(user, "Caster", "")):
            if data.GetParamCount() < 2:
                Parent.SendTwitchWhisper(user, settings["languageWrongSyntaxOfGiveCommand"])
            else:
                giveUsername = data.GetParam(1)
                giveAmount = str(data.GetParam(2))
                if "%" in giveAmount:
                    percent = int(giveAmount.replace("%", ""))
                    giveAmount = int(round(jackpotAmount / 100 * percent))
                else:
                    giveAmount = int(giveAmount)
                if giveAmount > jackpotAmount:
                    giveAmount = jackpotAmount
                Parent.SendTwitchMessage(settings["languageWinning"].format(giveUsername, giveAmount, Parent.GetCurrencyName()))
                SetJackpot((jackpotAmount - giveAmount))
                Parent.AddPoints(giveUsername, giveAmount)
        elif (data.GetParam(0) == settings["commandReset"] and Parent.HasPermission(user, "Caster", "")):
            SetJackpot(settings["startJackpot"])
            lastRound = 0
        elif (data.GetParam(0) == settings["commandEnableCooldown"] and Parent.HasPermission(user, "Caster", "")):
            globalCoolDown = 1
            Parent.SendTwitchMessage(settings["languageEnableCooldown"].format(settings["cooldown"]))
        elif (data.GetParam(0) == settings["commandDisableCooldown"] and Parent.HasPermission(user, "Caster", "")):
            globalCoolDown = 0
            Parent.SendTwitchMessage(settings["languageDisableCooldown"].format(settings["command"]))
    return


# ---------------------------------------
#	[Required] Tick Function
# ---------------------------------------
def Tick():
    return


def SetJackpot(jackpotValue):
    global settings, jackpotAmount
    if (jackpotValue <= 0):
        jackpotAmount = settings["startJackpot"]
        jackpotValue = jackpotAmount
        Parent.SendTwitchMessage(settings["languageJackpotRefill"].format(jackpotAmount, Parent.GetCurrencyName()))
    jackpotFile = os.path.join(os.path.dirname(__file__), settings['jackpotFileName'])
    file = open(jackpotFile, "w")
    file.write(str(int(jackpotValue)))
    file.close()
    return
