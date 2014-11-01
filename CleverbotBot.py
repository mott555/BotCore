import random
import re
from BotCore import BotCore
from cleverbot import Cleverbot

def privateMessageCallback(bot, mention, rawPostText, user):
    m = re.match(r"^clear history[.]*", rawPostText, re.IGNORECASE)
    if m:
        bot.conversations = {}
        message = "Bot conversation history cleared."
        message = bot.AppendUnique(message, mention)
        bot.ReplyTo(mention.topic_id, mention.post_number, message)
    else:
        mentionCallback(bot, mention, rawPostText, user)

def mentionCallback(bot, mention, rawPostText, user):
    # Parse out mention (and prior).
    m = re.match(r"@%s,\s*(.+)" % (bot.Login), rawPostText, re.IGNORECASE)
    if m:
        question = m.groups()[0]
        respondAsCleverbot(bot, mention, question, user)
      
def replyCallback(bot, mention, rawPostText, user):
    respondAsCleverbot(bot, mention, rawPostText, user)

def respondAsCleverbot(bot, mention, question, user):
    # Get Cleverbot instance for this topic.
    if mention.topic_id not in bot.conversations:
        bot.conversations[mention.topic_id] = Cleverbot()
    cleverbot = bot.conversations[mention.topic_id]
    
    # Capitalize first letter of user post.
    if (len(question) > 1):
        question = question[0].upper() + question[1:]
    else:
        question = question.capitalize()
        
    # Submit to Cleverbot API.
    message = cleverbot.ask(question)
    if message == "":
        return
    
    # Prepent original question as a quote.
    message = u'[quote="%s, post:%d, topic:%d"]%s[/quote]' % (mention.username, mention.post_number, mention.topic_id, question) + message
    bot.ReplyTo(mention.topic_id, mention.post_number, message)


if __name__ == "__main__":
    LOGIN = ""
    PASSWORD = ""
    
    bot = BotCore()
    bot.BotAdmin = ""
    bot.Help.append("**clear history:** (PM) Clears the bot's conversation history. One history is kept per topic that the bot participates in.")
    bot.AboutExtension = "CleverbotBot, a BotCore extension by @mott555.\n\nA simple mention followed by a comma will summon Cleverbot who will respond to your post. Everything prior to the mention will be ignored, allowing you to send a portion of your post to Cleverbot. Cleverbot will also respond to direct replies."
    bot.Login = LOGIN
    bot.Password = PASSWORD
    bot.LurkMode = True
    bot.MentionCallback = mentionCallback
    bot.PrivateMessageCallback = privateMessageCallback
    bot.ReplyCallback = replyCallback
    # Dictionary to store conversation history, one per topic.
    bot.conversations = {}    
    bot.run()

