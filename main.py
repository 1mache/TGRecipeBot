from threading import current_thread
import types
import telebot
from telebot import REPLY_MARKUP_TYPES, types
import arch
from arch import Ingredient, find_dish, find_user
import constants as c
import datetime as dt

bot = telebot.TeleBot(c.API_KEY)
arch.load_users()


QUIT_COMMAND = "quit"

def get_weekday():
    wd = dt.datetime.today().strftime("%w")
    return c.DAYS_NAMES[int(wd)]

def set_week_plan():
    pass

#===============ensure logic================
def ensure(message, question, func , *args, **kwargs):
    rkm = types.ReplyKeyboardMarkup(resize_keyboard= True, one_time_keyboard= True)
    yes_b = types.KeyboardButton("Yes")
    no_b = types.KeyboardButton("No")
    rkm.add(yes_b, no_b)
    if(question == None):
        msg = bot.reply_to(message, f"Your answer is {message.text}, is this correct?", reply_markup = rkm)
    else:
        msg = bot.reply_to(message, question, reply_markup = rkm)

    print(len(args))
    if(len(args) == 1): #if the func has only 1 argument that may be a command to use the "message" as an argument for func
        if(args[0] == ":next_step_message:"):
            bot.register_next_step_handler(msg, bool_answer_handler, func, message, **kwargs) 
            return
    #else
    bot.register_next_step_handler(msg, bool_answer_handler, func, *args, **kwargs)

def bool_answer_handler(message, func, *args, **kwargs):
    hide_markup = types.ReplyKeyboardRemove()
    if(message.text.lower() == "yes"):
        bot.send_message(message.chat.id, "OK.", reply_markup=hide_markup)
        func(*args, **kwargs)
    elif(message.text.lower() == "no"):
        bot.send_message(message.chat.id, "Command was cancelled.", reply_markup=hide_markup)
    else:
        bot.send_message(message.chat.id, "What? Thats not a Yes/No! Command was cancelled.", reply_markup=hide_markup)
#===============ensure logic================

#===============ingridient input logic==============
def string_toIngredient(input): #converts the string input of "ingregientName - quantity" into an ingredient object
    name, quantity,units = ("","","")
    
    need_edit = [name, quantity, units]
    counter = 0
    for i in range(len(input)):
        char = input[i]
        if(counter > 0 and char == " "):
            continue
        if(counter == 1 and not char.isdigit()):
            counter+=1
        if(char != "," and char != "-"):
            need_edit[counter] += char
        else:
            if(len(need_edit[counter])==0):
                print("Error")
            else:
                counter +=1
                continue

    name, quantity, units = (need_edit[0].strip(), need_edit[1], need_edit[2])

    if(name == "" or quantity == ""):
        return None

    return Ingredient(name, quantity, units)

def input_loop(message, dish_name,ingrlist):
    if(message.text == QUIT_COMMAND):
        loop_quit(message, dish_name, ingrlist)
    else:
        ingr = string_toIngredient(message.text)
        msg_text = "Please enter the next ingredient (name, quantity) or (name - quantity)"

        if(ingr != None):
            for i in ingrlist:
                if(i.name == ingr.name):
                    msg_text = "An ingredient with this name is already present in the list! Enter a different ingredient"
                    msg = bot.send_message(message.chat.id, msg_text)
                    bot.register_next_step_handler(msg,input_loop, dish_name, ingrlist )
                    return
            #else
            ingrlist.append(ingr)
        else:
            msg_text = "Format error! Please enter the ingredient in a format: 'name, quantity' or 'name - quantity'"
        msg = bot.send_message(message.chat.id, msg_text)
        bot.register_next_step_handler(msg,input_loop, dish_name, ingrlist )
    
def ingrdnt_loop_start(message):
    dish_name = message.text

    msg = bot.send_message(message.chat.id, f"Please enter the first ingredient for {dish_name} in a format 'name, quantity', " + 
     f"whenever you like to stop or if there are no more ingredients type '{QUIT_COMMAND}'. There cannot be two ingredients with the same name")
    bot.register_next_step_handler(msg,input_loop, dish_name, [])

def loop_quit(message, dish_name,ingrlist):
    if len(ingrlist) == 0: #if dish has 0 ingredients its invalid
        bot.send_message(message.chat.id ,f"Dish {dish_name} was cancelled, run /new_dish when you'd like to create another one")
    else:
        success_message = f"Successfully created a recipe for {dish_name}! The Ingredients are: \n" 
        for i in ingrlist:
            success_message += f"{str(i)}\n" 
        bot.send_message(message.chat.id, success_message)
        
        arch.new_dish(dish_name, ingrlist, message.chat.id)
#===============ingridient input logic==============

@bot.message_handler(commands=['start', 'help'])
def start(message):
    u = find_user(message.chat.id) 
    if (u == None): #tries to find user by this chat id and if there is none creates one
        arch.new_user(message.chat.id)
    
    bot.send_message(message.chat.id ,c.GREETINGS)

@bot.message_handler(commands= ["new_dish"])
def create_new_dish(message):
    msg = bot.send_message(message.chat.id, "Please enter the name of the dish")
    bot.register_next_step_handler(msg, ensure, None, ingrdnt_loop_start, ":next_step_message:")

@bot.message_handler(commands= ["my_dishes"] )
def get_dishes(message):
    text = ""
    user = find_user(message.chat.id)
    for dish in user.dishes:
        text += dish.name.capitalize()
        text += "\n"
    bot.send_message(message.chat.id, f"Your dishes are:\n{text}")

@bot.message_handler(commands= ["test_glist"] )
def test_glist(message):
    user = find_user(message.chat.id)
    print(arch.calculate_groceries([user.dishes[0], user.dishes[1]]))

@bot.message_handler(commands= ["show_ingredients"] )
def view_dish(message):
    request = message.text.split()
    if(len(request)>1):
        request.pop(0) #removes the command itself
        name = ""
        for word in request:
            name += f"{word} " #joins the rest of the words into a name
        d = find_dish(name, message.chat.id)
        if(d != None):
            text = f"{d.name}:\n"
            for ingr in d.ingrdnts:
                text += str(ingr)
                text += "\n"
            bot.send_message(message.chat.id, text)
        else:
            bot.send_message(message.chat.id, "You don't have a dish with that name, try again!")
    else:
        bot.send_message(message.chat.id, "You didn't specify the name of the dish to view!")

@bot.message_handler(commands= ["delete_dish"] )
def delete_dish(message):
    u = find_user(message.chat.id)
    request = message.text.split()
    if(len(request)>1):
        request.pop(0) #removes the command itself
        name = ""
        for word in request:
            name += f"{word} " #joins the rest of the words into a name
        d = find_dish(name, message.chat.id)
        if(d != None):
            ensure(message, f"Are you sure you want to delete the ingredient list for {d.name}?", delete_dish_from_user, u, d)
        else:
            bot.send_message(message.chat.id, "You don't have a dish with that name, try again!")
    else:
        bot.send_message(message.chat.id, "You didn't specify the name of the dish to delete!")


def delete_dish_from_user(u, d):
    u.remove_dish(d)
    bot.send_message(u.chat_id, f"{d.name.capitalize()} is no longer in your dishes list.")

#---------------------------schedule------------------------
@bot.message_handler(commands= ["set_plan_day"])
def set_plan_day(message):
    ikm = types.InlineKeyboardMarkup()
    for i in range(0,7):
        text = c.DAYS_NAMES[i].title()
        ikm.add(types.InlineKeyboardButton(text, callback_data= text))
    bot.send_message(message.chat.id, "Please type a name of the week day (in english) which will be your planning day", reply_markup=ikm)


@bot.callback_query_handler(func= lambda call: True)
def weekday_callback(call):
    if call.data.lower() in c.DAYS_NAMES.values():
        find_user(call.message.chat.id).change_planday(call.data)
        bot.send_message(call.message.chat.id, f"Your plan day was set to {call.data}")

@bot.message_handler(commands= ["my_plan_day"])
def get_plan_day(message):
    bot.send_message(message.chat.id, f"Your current plan day is {find_user(message.chat.id).plan_day}")

@bot.message_handler(commands=["my_schedule"])
def get_schedule(message):
    u = find_user(message.chat.id)
    text = ""
    if(len(u.schedule)==0):
        bot.send_message(message.chat.id, "Currently you dont have a schedule, /new_schedule to create one or wait for notification on your set plan day.")
        return    
    for day in u.schedule:
        dish_name = "None"
        if(day.dish != None):
            dish_name = day.dish.name.title()
        text += f"{day.name.title()} / {day.date}: {dish_name} \n"
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=["new_schedule"])
def new_schedule(message):
    u = find_user(message.chat.id)
    today_date = dt.datetime.today()
    today = arch.Day(c.DAYS_NAMES[int(today_date.strftime("%w"))], today_date)
    schedule = [today]
    for x in range(1,7):
        date = schedule[x-1].date + dt.timedelta(days=1)
        new_day = arch.Day(c.DAYS_NAMES[int(date.strftime("%w"))], date)
        print(str(new_day))
        schedule.append(new_day)
    
#---------------------------schedule------------------------


bot.polling(none_stop=True, interval=0)
