from BotCore import BotCore
from MarkovChain import MarkovChain
from datetime import datetime
import time, re, os

def mentionCallback(bot, mention, rawPostText, user):
    message = bot._markov.generateString()
    bot.ReplyTo(mention.topic_id, mention.post_number, message)
    
def privateMessageCallback(bot, mention, rawPostText, user):
    m = re.match(r"^set markov source (\w+)[.]*", rawPostText, re.IGNORECASE)
    if m:
        message = None
        username = m.groups()[0]
        secondsSinceLast = (datetime.utcnow() - bot.markovTimestamp).total_seconds()
        if secondsSinceLast < (60 * 30):
            message = "Markov source can only be set once per half hour. %d minutes remaining on cooldown." % (30 - (secondsSinceLast / 60))
            message = bot.AppendUnique(message, mention)
            bot.ReplyTo(mention.topic_id, mention.post_number, message)
        else:
            message = "Setting markov source to @%s's public posts. This may take a while. I will PM you when finished." % (username)
            message = bot.AppendUnique(message, mention)
            bot.ReplyTo(mention.topic_id, mention.post_number, message)
            bot.markovSource = username
            initializeMarkov(bot)
            time.sleep(5)
            message = "Markov source successfully changed to @%s's public posts." % (username)
            message = bot.AppendUnique(message, mention)
            bot.ReplyTo(mention.topic_id, mention.post_number, message)
    else:
        message = bot._markov.generateString()
        bot.ReplyTo(mention.topic_id, mention.post_number, message)
        

def initializeMarkov(bot):
    if os.path.isfile("./markovdb"):
        os.remove("./markovdb")
    bot._markov = MarkovChain()
    chain = ""
    posts = loadPosts(bot.markovSource, bot)
    for post in posts:
        chain += post + " "
    bot._markov.generateDatabase(chain)
    bot.markovTimestamp = datetime.utcnow()
    bot.AboutExtension = "MarkovBot, a BotCore extension by @mott555. Markov chain initialized to @%s's public post history." % (bot.markovSource)
    
def loadPosts(username, bot):
    getMorePosts = True
    offset = 0
    posts = []
    while getMorePosts:
        json = bot._get("/user_actions.json", offset=offset, username=username, filter=5, _=int(time.time() * 1000))
        actions = json[u'user_actions']
        print "Loaded %d posts from offset %d" % (len(actions), offset)
        if len(actions) > 0:
            for post in actions:
                posts.append(post[u'excerpt'])
            offset = len(posts)
        else:
            getMorePosts = False
    return posts
    
if __name__ == "__main__":
    LOGIN = ""
    PASSWORD = ""
    
    bot = BotCore()
    bot.BotAdmin = ""
    bot.markovSource = ""
    bot.Help.append("**set markov source [username]**: (PM) Re-initializes markov chain to username's public post history. Has a one-hour cooldown after being set.")
    bot.Help.append("**@%s**: (mention, PM) A simple mention/summon will cause the bot to post a sentence generated from its markov chain." % (LOGIN))
    bot.AboutExtension = "MarkovBot, a BotCore extension by @mott555. Markov chain not initialized."
    bot.Login = LOGIN
    bot.Password = PASSWORD
    bot.LurkMode = True
    bot.MentionCallback = mentionCallback
    bot.PrivateMessageCallback = privateMessageCallback
    bot.InitCallback = initializeMarkov
    bot.run()
