from BotCore import BotCore
import re, os

def pmCallback(bot, mention, rawPostText, user):
    
    isAdmin = mention.username.lower() == bot.BotAdmin.lower() or user.json["user"]["admin"] == "true" or user.json["user"]["moderator"] == "true"
    m = re.match(r"^add summon (\w+)[.]*", rawPostText, re.IGNORECASE)
    if m:
        username = m.groups()[0].lower()
        if username not in bot.UsersToSummon:
            message = None
            if isAdmin:
                bot.UsersToSummon.append(username)
                saveSummonList(bot)
                message = "@%s added to summon list." % username
            else:
                message = "You do not have permission to do that."
            message = bot.AppendUnique(message, mention)
            bot.ReplyTo(mention.topic_id, mention.post_number, message)
            return
            
    m = re.match(r"^remove summon (\w+)[.]*", rawPostText, re.IGNORECASE)
    if m:
        username = m.groups()[0].lower()
        if username in bot.UsersToSummon:
            message = None
            if isAdmin:
                bot.UsersToSummon.remove(username)
                saveSummonList(bot)
                message = "@%s removed from summon list." % username
            else:
                message = "You do not have permission to do that."
            message = bot.AppendUnique(message, mention)
            bot.ReplyTo(mention.topic_id, mention.post_number, message)
            return
            
    m = re.match(r"^clear summon list[.]*", rawPostText, re.IGNORECASE)
    if m:
        message = None
        if isAdmin:
            message = "Summon list cleared."
            bot.UsersToSummon = []
            saveSummonList(bot)
        else:
            message = "You do not have permission to do that."
        message = bot.AppendUnique(message, mention)
        bot.ReplyTo(mention.topic_id, mention.post_number, message)
        return
            
    m = re.match(r"^show summon list[.]*", rawPostText, re.IGNORECASE)
    if m:
        message = "**List of users to summon:**\n\n"
        for username in bot.UsersToSummon:
            message += "* @%s\n" % username
        message = bot.AppendUnique(message, mention)
        bot.ReplyTo(mention.topic_id, mention.post_number, message)
        return
		
	mentionCallback(bot, mention, rawPostText, user)
    
    
def mentionCallback(bot, mention, rawPostText, user):
    message = None
    if len(bot.UsersToSummon) == 0:
        message = "No, @%s, I refuse to do your bidding!" % mention.username
    else:
        summonList = ""
        if len(bot.UsersToSummon) == 1:
            summonList = "@%s" % bot.UsersToSummon[0]
        elif len(bot.UsersToSummon) == 2:
            summonList = "@%s and @%s" % (bot.UsersToSummon[0], bot.UsersToSummon[1])
        else:
            for index in range(0, len(bot.UsersToSummon) - 1):
                summonList += "@%s, " % bot.UsersToSummon[index]
            summonList += "and @%s" % bot.UsersToSummon[-1]
        message = "Yes, Master @%s, by your command I shall summon %s." % (mention.username, summonList)
    message = bot.AppendUnique(message, mention)
    bot.ReplyTo(mention.topic_id, mention.post_number, message)
    
def saveSummonList(bot):
    with open("./%s-summonList.txt" % LOGIN, "w") as file:
        for username in bot.UsersToSummon:
            file.write("%s\n" % username)

if __name__ == "__main__":
    LOGIN = ""
    PASSWORD = ""

    bot = BotCore()
    
    bot.BotAdmin = ""
    bot.Login = LOGIN
    bot.Password = PASSWORD
    bot.AboutExtension = "SummonBot, a BotCore extension by @mott555.\nThis bot can be summoned by simple mentions to respond and summon other bots."
    bot.Help.append("**add summon [username]:** (PM) Adds a user to the summon list. Only available to the bot owner and forum admins/mods.")
    bot.Help.append("**remove summon [username]:** (PM) Removes a user from the summon list. Only available to the bot owner and forum admins/mods.")
    bot.Help.append("**show summon list:** (PM) Shows the current summon list.")
    bot.Help.append("**clear summon list:** (PM) Removes all users from the summon list. Only available to the bot owner and forum admins/mods.")
    
    bot.UsersToSummon = []
    
    if os.path.isfile("./%s-summonList.txt" % LOGIN):
        with open("./%s-summonList.txt" % LOGIN, "r") as file:
            for line in file:
                bot.UsersToSummon.append(line.strip())

    bot.PrivateMessageCallback = pmCallback
    bot.MentionCallback = mentionCallback

    bot.run()

