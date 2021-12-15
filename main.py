
import types
import telebot
from telebot import types
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

def hide_kb_markup():
    return types.ReplyKeyboardRemove()

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
    hide_markup = hide_kb_markup()
    if(message.text.lower() == "yes"):
        bot.send_message(message.chat.id, "OK. 👌", reply_markup=hide_markup)
        func(*args, **kwargs)
    elif(message.text.lower() == "no"):
        bot.send_message(message.chat.id, "Command was cancelled.", reply_markup=hide_markup)
    else:
        bot.send_message(message.chat.id, "What? Thats not a Yes/No! 🤔 Command was cancelled.", reply_markup=hide_markup)
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
    if(message.text.lower() == QUIT_COMMAND):
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

@bot.message_handler(commands= ["ingredients"] )
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

#===========================DELETE DISH================================
@bot.message_handler(commands= ["delete_dish"] )
def delete_dish(message):
    u = find_user(message.chat.id)
    rkm = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for dish in u.dishes:
        rkm.add(types.KeyboardButton(dish.name.title()))
    msg = bot.send_message(message.chat.id, "Which dish would you like to delete?", reply_markup=rkm)
    bot.register_next_step_handler(msg, delete_check, u)

def delete_check(message, user):
    dish = arch.find_dish(message.text, message.chat.id)
    if dish != None :
        ensure(message, f"Are you sure you want to delete {dish.name.title()}", delete_dish_from_user, user, dish)
    else:
        bot.send_message(message.chat.id, "You dont have a dish with that name in your list", reply_markup= hide_kb_markup())

def delete_dish_from_user(u, d):
    u.remove_dish(d)
    bot.send_message(u.chat_id, f"{d.name.capitalize()} is no longer in your dishes list.")

#---------------------------schedule------------------------
@bot.message_handler(commands= ["set_plan_day"])
def set_plan_day(message):
    ikm = types.InlineKeyboardMarkup()
    for i in range(0,7):
        text = c.DAYS_NAMES[i].title()
        ikm.add(types.InlineKeyboardButton(text, callback_data= text + "_plan"))
    bot.send_message(message.chat.id, "Please type a name of the week day (in english) which will be your planning day", reply_markup=ikm)


@bot.callback_query_handler(func= lambda call: "_plan" in call.data)
def weekday_callback(call):
    data = call.data[:-5] #slices the _plan part
    find_user(call.message.chat.id).change_planday(call.data)
    bot.send_message(call.message.chat.id, f"Your plan day was set to {data}")

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

    ikm = types.InlineKeyboardMarkup()        
    for day in u.schedule:
        dishes_names = "None 🍽️"
        if(len(day.planned_dishes)!=0):
            dishes_names = ""
            for d in day.planned_dishes:
                dishes_names += d.name.title() + ", "
            dishes_names = dishes_names.strip()[:-1] #strips and slices the final coma off

        text += f"{day.name.title()} / {day.date.strftime(c.DATE_FORMAT)}: {dishes_names} \n"

        ikm.add(types.InlineKeyboardButton(day.name.title(), callback_data= day.name+"_day_edit"))
    
    text += """-------------
Select one of the days to clear/add a dish!🍴
/groceries to create a grocery list for this schedule 🛒"""

    bot.send_message(message.chat.id, text, reply_markup=ikm)

@bot.callback_query_handler(func= lambda call: "_day_edit" in call.data)
def setdish_callback(call):
    data = call.data[:-9] #slices the identifier
    if data in c.DAYS_NAMES.values():
        print("asking for dishname")
        ask_for_dishname(call.message.chat.id,data)
    else:
        print("Day upper case error")

def ask_for_dishname(chat_id, day_name):
    u = find_user(chat_id)
    rkm = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for dish in u.dishes:
        rkm.add(types.KeyboardButton(dish.name.title()))
    
    msg = bot.send_message(chat_id, f"Please give me a dish to put on {day_name.title()}! ('clear' for clearing day)", reply_markup=rkm)
    bot.register_next_step_handler(msg, setday_finalstep, day_name)

def setday_finalstep(message, day_name):
    hide = hide_kb_markup()
    u = find_user(message.chat.id)
    dish_name = message.text.strip().lower()
    if(dish_name == "clear"): 
        u.clearday(day_name)
        bot.send_message(message.chat.id, f"Successfully cleared {day_name.title()}", reply_markup=hide)
        return
   
    found_dish = arch.find_dish(dish_name, message.chat.id)
    if(found_dish != None):
        u.add_dish_to_schedule(day_name, found_dish)
        bot.send_message(message.chat.id, f"Successfully scheduled {dish_name.title()} on {day_name.title()} 🍴", reply_markup=hide)
        return

    bot.send_message(message.chat.id, f"This dish is not in your dish list 🤔 please try again! ")
    ask_for_dishname(message.chat.id, day_name)

@bot.message_handler(commands=["new_schedule"])
def new_schedule(message):
    u = find_user(message.chat.id)
    today_date = dt.datetime.today()
    today = arch.Day(c.DAYS_NAMES[ int(today_date.strftime("%w")) ], today_date)
    schedule = [today]
    for x in range(1,7):
        date = schedule[x-1].date + dt.timedelta(days=1)
        new_day = arch.Day(c.DAYS_NAMES[ int(date.strftime("%w")) ], date)
        schedule.append(new_day)
    
    u.add_schedule(schedule) 
    bot.send_message(message.chat.id, f"Successfully created a schedule starting today {today_date.strftime(c.DATE_FORMAT)}")

@bot.message_handler(commands=["groceries"])
def groceries(message):
    u = find_user(message.chat.id)
    u.clear_groceries()
    if(len(u.grocery_list)==0):
        if(len(u.schedule)!= 0):
            u.add_grocery_list(arch.calculate_groceries(u))
            if(len(u.grocery_list)==0):
                bot.send_message(message.chat.id, "Your schedule is empty 🤔 ... Try filling it first")
                return
        else:
            bot.send_message(message.chat.id, "Your schedule is empty 🤔 ... Try filling it first")
            return

    text = "Your grocery list 🛒 is :"
    for key in u.grocery_list.keys():
        text+= f"\n{key.title()} -- {u.grocery_list[key]}"
    bot.send_message(message.chat.id, text)
    
#---------------------------schedule------------------------


bot.polling(none_stop=True, interval=0)
