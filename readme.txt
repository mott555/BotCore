BotCore + Mott555's Bot Pack

License:
Do whatever you want with this code, I don't care. No warranty or guarantees about anything.

About BotCore:
BotCore is an extensible Discourse bot with advanced features which can be used to create a bot which responds to mentions,
replies, and private messages. It is designed as an API, you will import BotCore.py into your script and add a few functions 
to make it work.

Features:
* Allows you to determine if the user is the bot owner, forum admin or moderator.
* Provides you with the username and raw post text of the summoning post, along with the Discourse JSON data of the user.
* Caches JSON data for users, avoiding excessive network calls to look up user info.
* Easy hooks to add initialization code and respond to mentions, replies, and private messages.
* Some options can be configured at runtime by PM'ing the bot.
* Lurk Mode, which prevents the bot from interacting with public posts, allowing it to be shut down or tested via PM.
* Configurable minimum trust levels for interaction, preventing new users (spammers and trolls) from triggering bots.
* Configurable ignore lists to allow your bots to ignore specific users and stay out of specific topics.
* Simple about screen (accessible via PM) to display the bot's version, purpose, status, and owner.
* Simple help screen (accessible via PM) to display the bot's supported commands and syntax.

Requirements:
BotCore is written in Python 2.7.8 and should be reasonably cross-compatible, I developed it on Windows but deploy finished bots to Ubuntu.
The requests library is a dependency, you can get it at http://docs.python-requests.org/en/latest/user/install/
Note whatever process is operating the bot must have read/write access to the script directory, it will store some simple configuration data
in text files there.

Included Bots:
SampleBot.py - Start here for the basics, this is a well-commented extension and will get you started. PM "help" or "about" to the bot to see its details and commands.
CleverbotBot.py - Utilizes the Cleverbot web API to allow Discourse users to communicate with Cleverbot on the forum.
MarkovBot.py - Uses Markov chains initialized with the post history of specific Discourse users to provide nonsense responses when summoned.
SummonBot.py - Simple bot which will summon other Discourse users when summoned.
