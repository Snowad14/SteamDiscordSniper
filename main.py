import json
import steam.webauth as wa
import discord
import yaml

print("""
  /$$$$$$   /$$                                        /$$$$$$            /$$                              
 /$$__  $$ | $$                                       /$$__  $$          |__/                              
| $$  \__//$$$$$$    /$$$$$$   /$$$$$$  /$$$$$$/$$$$ | $$  \__/ /$$$$$$$  /$$  /$$$$$$   /$$$$$$   /$$$$$$ 
|  $$$$$$|_  $$_/   /$$__  $$ |____  $$| $$_  $$_  $$|  $$$$$$ | $$__  $$| $$ /$$__  $$ /$$__  $$ /$$__  $$
 \____  $$ | $$    | $$$$$$$$  /$$$$$$$| $$ \ $$ \ $$ \____  $$| $$  \ $$| $$| $$  \ $$| $$$$$$$$| $$  \__/
 /$$  \ $$ | $$ /$$| $$_____/ /$$__  $$| $$ | $$ | $$ /$$  \ $$| $$  | $$| $$| $$  | $$| $$_____/| $$      
|  $$$$$$/ |  $$$$/|  $$$$$$$|  $$$$$$$| $$ | $$ | $$|  $$$$$$/| $$  | $$| $$| $$$$$$$/|  $$$$$$$| $$      
 \______/   \___/   \_______/ \_______/|__/ |__/ |__/ \______/ |__/  |__/|__/| $$____/  \_______/|__/      
                                                                             | $$                          
                                                                             | $$                          
                                                                             |__/                                                
""")

stream = open("info.yaml", 'r')
content = yaml.safe_load(stream)

discordToken = content["DiscordToken"]
steamUsername = content["SteamUsername"]
steamPassword = content["SteamPassword"]
webhook = discord.Webhook.from_url(content["WebHook"], adapter=discord.RequestsWebhookAdapter())

# login to steam account

user = wa.WebAuth(steamUsername, steamPassword)
try:
    user.login()
except wa.EmailCodeRequired:
    print("give email code")
    code = input()
    user.login(email_code=code)
except wa.TwoFactorCodeRequired:
    print("give 2FA code")
    code = input()
    user.login(twofactor_code=code)
sessionid = user.session.cookies.get_dict()["sessionid"] # get session ID of the steam account

print("Steam is logged")

def check(message): # function to check if string is a steam code
    good = []
    world = message.split()
    for string in world:
        if (len(string) == 17 and string.find('-') == 5 and string.count('-') == 2): # to change, but work
            good.append(string)
    return good

def claim(code, sessionid): # function to claim code
    r = user.session.post('https://store.steampowered.com/account/ajaxregisterkey/', data={'product_key': code, 'sessionid': sessionid})
    response = json.loads(r.text)
    if response["success"] == 1:
        for item in response["purchase_receipt_info"]["line_items"]:
            print("[ Redeemed ]", item["line_item_description"])
            if webhook != "":
                try:
                    webhook.send("@everyone [ Redeemed ]", item["line_item_description"])
                except:
                    print("Invalid WebHook")
    else:
        errorCode = response["purchase_result_details"]
        sErrorMessage = ""
        if errorCode == 14:
            sErrorMessage = 'The product code you\'ve entered is not valid. Please double check to see if you\'ve mistyped your key. I, L, and 1 can look alike, as can V and Y, and 0 and O.'
        elif errorCode == 15:
            sErrorMessage = 'The product code you\'ve entered has already been activated by a different Steam account. This code cannot be used again. Please contact the retailer or online seller where the code was purchased for assistance.'
        elif errorCode == 53:
            sErrorMessage = 'There have been too many recent activation attempts from this account or Internet address. Please wait and try your product code again later.'
        elif errorCode == 13:
            sErrorMessage = 'Sorry, but this product is not available for purchase in this country. Your product key has not been redeemed.'
        elif errorCode == 9:
            sErrorMessage = 'This Steam account already owns the product(s) contained in this offer. To access them, visit your library in the Steam client.'
        elif errorCode == 24:
            sErrorMessage = 'The product code you\'ve entered requires ownership of another product before activation.\n\nIf you are trying to activate an expansion pack or downloadable content, please first activate the original game, then activate this additional content.'
        elif errorCode == 36:
            sErrorMessage = 'The product code you have entered requires that you first play this game on the PlayStation®3 system before it can be registered.\n\nPlease:\n\n- Start this game on your PlayStation®3 system\n\n- Link your Steam account to your PlayStation®3 Network account\n\n- Connect to Steam while playing this game on the PlayStation®3 system\n\n- Register this product code through Steam.'
        elif errorCode == 50:
            sErrorMessage = 'The code you have entered is from a Steam Gift Card or Steam Wallet Code. Browse here: https://store.steampowered.com/account/redeemwalletcode to redeem it.'
        else:
            sErrorMessage = 'An unexpected error has occurred.  Your product code has not been redeemed.  Please wait 30 minutes and try redeeming the code again.  If the problem persists, please contact <a href="https://help.steampowered.com/en/wizard/HelpWithCDKey">Steam Support</a> for further assistance.'
        print("[ Error ]", sErrorMessage)

client = discord.Client(status=discord.Status.online)

@client.event
async def on_ready():
    print("Discord is connected ({0.user})".format(client))

@client.event
async def on_message(message):
        if(message.author.bot):
            return;
        async for message in message.channel.history(limit=1):
            code = check(message.content)
            for string in code:
                print("Code sniped : " + string)
                claim(string, sessionid)

client.run(discordToken, bot=False)
