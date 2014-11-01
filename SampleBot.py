from BotCore import BotCore
import re

def initCallback(bot):
    print "Bot initialized"

def pmCallback(bot, mention, rawPostText, user):
    # Mention has these fields.
    username = mention.username
    topicID = mention.topic_id
    postNumber = mention.post_number
    notificationType = mention.notification_type
    
    # User object is JSON data retrieved from "/users/username.json", look there
    # for reference if you need to access additional user data.
    
    # Implement the Echo command.
    m = re.match(r"^echo (.+)", rawPostText, re.IGNORECASE)
    if (m):
        bot.ReplyTo(topicID, postNumber, m.groups()[0])
    else:
        bot.ReplyTo(topicID, postNumber, bot.AppendUnique("Regex failed?", mention))
    
def replyCallback(bot, mention, rawPostText, user):
    message = "I'm alive!!!"
    
    # AppendUnique puts the post ID and topic ID inside an HTML comment to
    # bypass Discourse's "Body is too similar to recent post" toaster.
    message = bot.AppendUnique(message, mention)
    bot.ReplyTo(mention.topic_id, mention.post_number, message)
    
def mentionCallback(bot, mention, rawPostText, user):
    message = "I'm alive!!!"
    message = bot.AppendUnique(message, mention)
    bot.ReplyTo(mention.topic_id, mention.post_number, message)

if __name__ == "__main__":
    LOGIN = ""
    PASSWORD = ""

    bot = BotCore()
    
    # BotAdmin must be set to your Discourse username to tell the bot who owns it. 
    bot.BotAdmin = ""
    
    # Minimum trust level to interact with the bot. Defaults to 2 if not set. If a user below
    # this trust level tries to interact with the bot, the callbacks will not be called, unless
    # said user is the bot owner, forum admin, or forum moderator.
    # BotCore will cache this in a local file, if present that setting will override this one.
    # bot.MinTrustLevel = 2
    
    # Discourse login details for the bot's account. Login value is also used for local
    # cache filenames (ignore list).
    bot.Login = LOGIN
    bot.Password = PASSWORD
        
    # URL to the Discourse instance, defaults to "http://what.thedailywtf.com" if not set.
    # Changing this is not recommended.
    # bot.BaseUrl = "http://what.thedailywtf.com"
    
    # Adds extra information to the bot's about screen.
    bot.AboutExtension = "SampleBot, a sample BotCore extension by @mott555."
    
    # If LurkMode is true, the bot will only respond to PM's, ignoring mentions and replies.
    # It will still consume notifications.
    # This defaults to true. It's a good idea to start in LurkMode and later disable LurkMode by
	# issuing a PM command to the bot when you're ready to make it act publicly.
    # bot.LurkMode = False
    
    # Hook up callbacks for the notifications you are interested in.
    bot.PrivateMessageCallback = pmCallback
    bot.ReplyCallback = replyCallback
    bot.MentionCallback = mentionCallback
    
    # You can append additional items to the bot's help screen. Note you must still
    # implement the command in one of the callback methods. You should also note what
    # methods the command supports (PM, reply, mention).
    bot.Help.append("**echo [message]**: (PM) Echoes a message back to you.")
    
    # Hook up an initialize callback if needed. This is called after the bot logs in
    # but before it responds to notifications.
    bot.InitCallback = initCallback
    
    # Start the bot!
    bot.run()