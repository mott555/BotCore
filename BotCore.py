from collections import namedtuple
import os, random, re, requests
from time import time, sleep
from datetime import datetime

BOT_VERSION = "0.5"

NOTIFICATION_TYPE_MENTION = 1
NOTIFICATION_TYPE_REPLY = 2
NOTIFICATION_TYPE_PM = 6

class BotCore(object):
    """
    An extensible Discourse bot.
    """
    
    Login = None
    Password = None
    InitCallback = None
    BotAdmin = None
    AboutExtension = None
    BaseUrl = "http://what.thedailywtf.com"
    
    MentionCallback = None
    PrivateMessageCallback = None
    ReplyCallback = None
    
    MinTrustLevel = 2
    IgnoredUsers = []
    IgnoredTopics = []
    UserCache = []
    LurkMode = True
    Help = ["**about**: (PM) Shows bot info.",
            "**help**: (PM) Shows this help screen.",
            "**ignore topic [topicID]**: (PM) Adds topic to ignore list so the bot will not respond to summons there.",
            "**stop ignoring topic [topicID]**: (PM) Removes topic from ignore list.",
            "**ignore user [username]**: (PM) Adds username to ignore list, bot will not respond to summons by that user.",
            "**stop ignoring user [username]**: (PM) Removes username from ignore list.",
            "**show ignore list**: (PM) Shows list of ignored topics and users.",
            "**set trustlevel [number]**: (PM) Changes minimum trust level required to interact with the bot. Only available to the bot owner or forum admins/moderators.",
            "**lurk mode on**: (PM) Puts bot in Lurk Mode. Bot will only respond to PM's, not public summons.",
            "**lurk mode off**: (PM) Disables Lurk Mode."]
            
    _currentNotificationType = None

    class WorseThanFailure(Exception):
        pass

    Mention = namedtuple('Mention', ['username', 'topic_id', 'post_number', 'notification_type'])
    Post = namedtuple('Post', ['number', 'id', 'can_like', 'message', 'poster',
        'poster_id'])
    CachedUser = namedtuple('CachedUser', ['name', 'json', 'timestamp'])
        
    def __init__(self):
        self._session = requests.Session()
        self._session.headers['X-Requested-With'] = "XMLHttpRequest"
        self._client_id = self._get_client_id()
        self._bus_registrations = {}
        self._bus_callbacks = {}

    def run(self):
        if self.BotAdmin is None or self.BotAdmin == "":
            raise self.WorseThanFailure("WhatBot.BotAdmin must be set!")
        if self.Login is None or self.Password is None or self.Login == "" or self.Password == "":
            raise self.WorseThanFailure("Bot login details not set!")
        # Get the CSRF token
        res = self._get("/session/csrf", _=int(time() * 1000))
        self._session.headers['X-CSRF-Token'] = res[u'csrf']

        # Login
        res = self._post("/session", login=self.Login, password=self.Password)
        if u'error' in res:
            raise self.WorseThanFailure(res[u'error'].encode('utf8'))

        my_uid = res[u'user'][u'id']

        self._bus_registrations["/notification/%d" % my_uid] = -1
        self._bus_callbacks["/notification/%d" % my_uid] = self._notif_cb

        self._session.headers['X-SILENCE-LOGGER'] = "true"
        
        # Load persistent ignore list from disk.
        if (os.path.isfile("./%s-ignore-users.txt" % self.Login)):
            with open("./%s-ignore-users.txt" % self.Login, 'r') as file:
                for line in file:
                    self.IgnoredUsers.append(line.strip())
                    
        # Load persistent ignore list from disk.
        if (os.path.isfile("./%s-ignore-topics.txt" % self.Login)):
            with open("./%s-ignore-topics.txt" % self.Login, 'r') as file:
                for line in file:
                    self.IgnoredTopics.append(int(line.strip()))
                    
        if (os.path.isfile("./%s-trust.txt" % self.Login)):
            with open("./%s-trust.txt" % self.Login, 'r') as file:
                self.MinTrustLevel = int(file.read())
        
        if self.InitCallback:
            self.InitCallback(self)
        
        self._handle_notifications()

        print "Entering main loop"
        while True:
            data = self._post("/message-bus/%s/poll" % self._client_id,
                **self._bus_registrations)

            for message in data:
                channel = message[u'channel']
                if channel in self._bus_registrations:
                    message_id = message[u'message_id']
                    self._bus_registrations[channel] = message_id
                    self._bus_callbacks[channel](message[u'data'])
                if channel == u"/__status":
                    for key, value in message[u'data'].iteritems():
                        if key in self._bus_registrations:
                            self._bus_registrations[key] = value

    def _notif_cb(self, message):

        count = message[u'unread_private_messages'] + message[u'unread_notifications']
        if count > 0:
            self._handle_notifications()

    def _handle_notifications(self):
        for mention in self._get_mentions():

            self._mark_as_read(mention.topic_id, mention.post_number)
            
            rawPostText = self._get_text("/raw/%d/%d" % (mention.topic_id, mention.post_number))
            user = self._getUserFromCache(mention.username)
            # Ignore summon if user is ignored or user does not have the required trust level.
            if user.json["user"]["trust_level"] < self.MinTrustLevel or mention.username.lower() in self.IgnoredUsers:
                # Extra check, even if user is ignored or below trust level, allow commands if this is a PM and 
                # the user is a moderator, admin, or the bot owner.
                if not(mention.notification_type == NOTIFICATION_TYPE_PM and (user.json["user"]["admin"] == "true" or user.json["user"]["moderator"] == "true" or mention.username.lower() == self.BotAdmin.lower())):
                    sleep(5)
                    continue
                
            if mention.topic_id in self.IgnoredTopics:
                sleep(5)
                continue
            
            callCallback = True
            
            # Cache here so extensions don't have to pass notification type back into the reply method.
            self._currentNotificationType = mention.notification_type
            
            # Parse to see if this is a special command handled by the core bot code.
            if mention.notification_type == NOTIFICATION_TYPE_PM:
                
                m = re.match(r"^ignore topic ([0-9]+)[.]*", rawPostText, re.IGNORECASE)
                if m:
                    topicID = int(m.groups()[0])
                    if topicID not in self.IgnoredTopics:
                        self.IgnoredTopics.append(topicID)
                        message = "Added topic %s/t/topic/%d to ignore list." % (self.BaseUrl, topicID)
                        message = self.AppendUnique(message, mention)
                        self.ReplyTo(mention.topic_id, mention.post_number, message)
                        callCallback = False
                        continueCommandParsing = False
                        m = None
                        self._saveIgnore()
                    
                m = re.match(r"^stop ignoring topic ([0-9]+)[.]*", rawPostText, re.IGNORECASE)
                if m:
                    topicID = int(m.groups()[0])
                    if topicID in self.IgnoredTopics:
                        self.IgnoredTopics.remove(topicID)
                        message = "Removed topic %s/t/topic/%d from ignore list." % (self.BaseUrl, topicID)
                        message = self.AppendUnique(message, mention)
                        self.ReplyTo(mention.topic_id, mention.post_number, message)
                        callCallback = False
                        m = None
                        self._saveIgnore()
                    
                m = re.match(r"^ignore user (\w+)[.]*", rawPostText, re.IGNORECASE)
                if m:
                    username = m.groups()[0].lower()
                    if username not in self.IgnoredUsers:
                        message = None
                        if username.lower() == self.BotAdmin.lower():
                            message = "@%s is the bot admin and cannot be added to the ignore list." % (username)
                        else:
                            self.IgnoredUsers.append(username)
                            message = "Added @%s to ignore list." % (username)
                        message = self.AppendUnique(message, mention)
                        self.ReplyTo(mention.topic_id, mention.post_number, message)
                        callCallback = False
                        m = None
                        self._saveIgnore()
                    
                m = re.match(r"^stop ignoring user (\w+)[.]*", rawPostText, re.IGNORECASE)
                if m:
                    username = m.groups()[0].lower()
                    if username in self.IgnoredUsers:
                        self.IgnoredUsers.remove(username)
                        message = "Removed @%s from ignore list." % (username)
                        message = self.AppendUnique(message, mention)
                        self.ReplyTo(mention.topic_id, mention.post_number, message)
                        callCallback = False
                        m = None
                        self._saveIgnore()
                    
                m = re.match(r"^show ignore list[.]*", rawPostText, re.IGNORECASE)
                if m:
                    message = "**Ignored Users**\n\n"
                    for u in self.IgnoredUsers:
                        message += "- @" + u + "\n"
                    message += "\n**Ignored Topics**\n\n"
                    for t in self.IgnoredTopics:
                        message += "- %s/t/topic/%d\n" % (self.BaseUrl, t)
                    message = self.AppendUnique(message, mention)
                    self.ReplyTo(mention.topic_id, mention.post_number, message)
                    callCallback = False
                    m = None
                    
                m = re.match(r"^about[.]*", rawPostText, re.IGNORECASE)
                if m:
                    message = "BotCore version %s, by @mott555\n" % (BOT_VERSION)
                    if self.AboutExtension:
                        message += self.AboutExtension + "\n"
                    message += "This bot is owned by @%s.\n" % (self.BotAdmin)
                    message += "\n"
                    if (self.LurkMode):
                        message += "Bot is in lurk mode, I will respond to PM's but not public posts.\n"
                    else:
                        message += "Bot is in public mode, I will respond to any summons I have access to.\n"
                    message += "Minimum Trust Level: %d\n" % (self.MinTrustLevel)
                    message = self.AppendUnique(message, mention)
                    self.ReplyTo(mention.topic_id, mention.post_number, message)
                    callCallback = False
                    m = None
                    
                m = re.match(r"^help[.]*", rawPostText, re.IGNORECASE)
                if m:
                    message = "\n\n**Supported Commands:**\n\n"
                    for h in self.Help:
                        message += "- %s\n" % (h)
                    message = self.AppendUnique(message, mention)
                    self.ReplyTo(mention.topic_id, mention.post_number, message)
                    callCallback = False
                    m = None
                    
                m = re.match(r"^lurk mode (on|off)[.]*", rawPostText, re.IGNORECASE)
                if m:
                    mode = m.groups()[0]
                    message = None
                    if mode == "on":
                        self.LurkMode = True
                        message = "Lurk Mode enabled."
                    else:
                        self.LurkMode = False
                        message = "Lurk Mode disabled."
                    message = self.AppendUnique(message, mention)
                    self.ReplyTo(mention.topic_id, mention.post_number, message)
                    callCallback = False
                    m = None
                    
                m = re.match(r"^set trustlevel ([0-4]+)[.]*", rawPostText, re.IGNORECASE)
                if m:
                    trust = int(m.groups()[0])
                    message = None
                    if mention.username.lower() == self.BotAdmin.lower() or user.json["user"]["admin"] == "true" or user.json["user"]["moderator"] == "true":
                        self.MinTrustLevel = trust
                        message = "Minimum trust level changed to %d." % (trust)
                        with open("./%s-trust.txt" % self.Login, 'w') as file:
                            file.write(trust)
                    else:
                        message = "You do not have permission to change that setting."
                    self.AppendUnique(message, mention)
                    self.ReplyTo(mention.topic_id, mention.post_number, message)
                    callCallback = False
                    m = None
            
            if callCallback:
                if mention.notification_type == NOTIFICATION_TYPE_PM and self.PrivateMessageCallback:
                    self.PrivateMessageCallback(self, mention, rawPostText, user.json)
                if mention.notification_type == NOTIFICATION_TYPE_REPLY and self.ReplyCallback and not self.LurkMode:
                    self.ReplyCallback(self, mention, rawPostText, user.json)
                if mention.notification_type == NOTIFICATION_TYPE_MENTION and self.MentionCallback and not self.LurkMode:
                    self.MentionCallback(self, mention, rawPostText, user.json)

            sleep(5)
            
    def _saveIgnore(self):
        with open("./%s-ignore-users.txt" % self.Login, 'w') as file:
            for user in self.IgnoredUsers:
                file.write("%s\n" % user)
        with open("./%s-ignore-topics.txt" % self.Login, 'w') as file:
            for topic in self.IgnoredTopics:
                file.write("%d\n" % topic)
            
    def AppendUnique(self, message, mention):
        return "%s<!-- t%d p%d -->" % (message, mention.topic_id, mention.post_number)

    def _getUserFromCache(self, username):
        cachedUser = None
        for u in self.UserCache:
            if u.name == username:
                cachedUser = u
        if cachedUser is None or (datetime.utcnow() - cachedUser.timestamp).total_seconds() > (60 * 30):
            if cachedUser in self.UserCache:
                self.UserCache.remove(cachedUser)
            userDetails = self._get("/users/%s.json" % (username), _=int(time() * 1000))
            cachedUser = self.CachedUser(name=username, json=userDetails, timestamp=datetime.utcnow())
            self.UserCache.append(cachedUser)
        return cachedUser
            

    def ReplyTo(self, topic_id, post_number, raw_message):
        # No idea what happens if we mix these up
        archetype = 'private_message' if self._currentNotificationType == NOTIFICATION_TYPE_PM else 'regular'

        return self._post("/posts", raw=raw_message, topic_id=topic_id,
            reply_to_post_number=post_number,
            archetype=archetype
        )

    def _mark_as_read(self, topic_id, post_number):
        # Send fake timings
        # I hate special chars in POST keys
        kwargs = {
            'topic_id': topic_id,
            'topic_time': 400, # msecs passed on topic (I think)
            'timings[%d]' % post_number: 400 # msecs passed on post (same)
        }

        self._post("/topics/timings", **kwargs)


    def _get_mentions(self):
        watched_types = [NOTIFICATION_TYPE_MENTION, NOTIFICATION_TYPE_REPLY, NOTIFICATION_TYPE_PM]

        for notification in self._get("/notifications", _=int(time() * 1000)):
            if (notification[u'notification_type'] in watched_types and
                notification[u'read'] == False):
                data = notification[u'data']
                yield self.Mention(username=data[u'original_username'],
                    topic_id=notification[u'topic_id'],
                    post_number=notification[u'post_number'],
                    notification_type=notification[u'notification_type'])

    @staticmethod
    def _get_client_id():
        def _replace(letter):
            val = random.randrange(0, 16)
            if letter == "x":
                val = (3 & val) | 8
            return "%x" % val

        return re.sub('[xy]', _replace, "xxxxxxxxxxxx4xxxyxxxxxxxxxxxxxxx")

    def _get(self, url, **kwargs):
        for _ in xrange(30):
            r = self._session.get(self.BaseUrl + url, params=kwargs)
            if r.status_code < 500:
                break
            print "GET request returned code %d, retrying" % r.status_code
            sleep(2)
        r.raise_for_status()
        return r.json()

    def _post(self, url, **kwargs):

        for _ in xrange(30):
            r = r = self._session.post(self.BaseUrl + url, data=kwargs)
            if r.status_code < 500 and r.status_code != 429:
                break
            print "POST request returned code %d, retrying" % r.status_code
            if r.status_code == 429:
                sleep(5)
            else:
                sleep(2)

        if r.status_code == 422:
            raise self.WorseThanFailure(u",".join(r.json()[u'errors']))
        r.raise_for_status()
        if r.headers['Content-type'].startswith('application/json'):
            return r.json()
        return r.content
        
    def _get_text(self, url, **kwargs):
        for _ in xrange(30):
            r = self._session.get(self.BaseUrl + url, params=kwargs)
            if r.status_code < 500:
                break
            print "GET request returned code %d, retrying" % r.status_code
            sleep(2)
        r.raise_for_status()
        return r.text
           

if __name__ == '__main__':
    WhatBot().run()

