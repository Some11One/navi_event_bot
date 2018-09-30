from telebot.types import LabeledPrice
from telebot.types import ShippingOption

"""

Bot and NaviAddress settings

"""

# e-mail & password for naviaddress map api
email = ''
password = ''

# telegram token
token = ''

# telegram payment token
payment_token = ''

# global variables used in bot
user_state = None
navi_container, navi_naviaddress = '', ''
event_name, event_link = '', ''
event_money = ''
user_name, user_mail = '', ''
weights = []
step_description = ''
steps = []
image_counter = 0

# additional payment variables
settings_global = {
    "cluster_numbers": None
}
shipping_options = [
    ShippingOption(id='instant', title='1').add_price(LabeledPrice('1', 1000)),
    ShippingOption(id='pickup', title='2').add_price(LabeledPrice('2', 300))]
