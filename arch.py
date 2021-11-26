import pickle
import datetime
import constants as c

G = ("g", "gram", "gr")
KG = ("kg", "kilogram")
ML = ("ml", "mililiter")
L = ("l", "liter")
SPOONS = ("spoons", "spoon")
TEASPOONS = ("teaspoons", "teaspoon")
STANDART_UNITS = [G, KG, ML, L, SPOONS, TEASPOONS]
#---------------users_logic---------------
users = []

def save_users():
    pickle_out = open("users.pickle","wb")
    pickle.dump(users, pickle_out)
    pickle_out.close()

def saver(func):
    def wrapper(*args, **kwargs):
        func(*args, **kwargs)
        save_users()
    return wrapper

def load_users():
    try:
        global users
        pickle_in = open("users.pickle","rb")
        users = pickle.load(pickle_in)
        pickle_in.close()
    except:
        print("first time exception")
        save_users()
        load_users()

class User():
    def __init__(self, chat_id, dishes = [], schedule = [], plan_day = "Friday"):
        self.chat_id= chat_id
        self.dishes= dishes
        self.schedule = schedule
        self.plan_day= plan_day

    def __str__(self) -> str:
        return f"ChatID: {self.chat_id} PlanDay: {self.plan_day}"

    @saver
    def change_planday(self, plan_day):
        self.plan_day = plan_day
    
    @saver
    def add_dish(self, dish):
        self.dishes.append(dish)
    
    @saver 
    def remove_dish(self,dish):
        self.dishes.remove(dish)

    @saver 
    def add_schedule(self, schedule):
        self.schedule = schedule
    
    @saver 
    def set_dish(self, day_name, dish):
        if(len(self.schedule) != 0):
            for day in self.schedule:
                if day.name == day_name:
                    day.assign_dish(dish)
        else:
            print("Error")

def find_user(chat_id) -> User:
    global users 
    for u in users:
        if(u.chat_id == chat_id):
            return u
    #if nothing was found:
    return None
    
#---------------users_logic---------------    
def sum_of_quantities(given_str, given_value, given_units):

    components = given_str.split("+")
    for count,element in enumerate(components):
        numunit = element.strip() #gets rid of whitespaces
        numunit = numunit.split(" ")
        if(len(numunit) == 2):
            value_in_str = numunit[0]
            units_in_str = numunit[1]
            if(units_in_str == given_units):
                components[count] = f"{int(value_in_str)+given_value} {units_in_str}"
                return " + ".join(components)  
            
            # for i in STANDART_UNITS:
            #     if(given_units in i):
            #         print("gg " + given_units + " in " + i[0])
            #         components[count] = f"{int(value_in_str)+given_value} {i[0]}"
            #         return " + ".join(components)  
        else:
            return "error"

    return f"{given_str} + {given_value} {given_units}"
          
class Ingredient:
    def __init__(self, name, quantity, units):
        self.name = name.lower()
        try:
            self.quantity  = int(quantity)
        except:
            print(f"Type exception for trying to convert{quantity} to int")
            self.quantity = "error"
        self.units = units.lower()
    def __str__(self) -> str:
        return (f"{self.name.title()} - {self.quantity} {self.units}")

class Dish: 
    def __init__(self, name, ingrdnts):
        self.name = name
        self.ingrdnts = ingrdnts

class Day:
    def __init__(self, name, date):
        self.name = name.lower()
        self.date = date
        self.dish = None

    def __str__(self) -> str:
        #debug
        return(f"{self.name.title()}, {self.date.strftime(c.DATE_FORMAT)}")

    def assign_dish(self, dish):
        self.dish = dish
    
#---------------interaction---------------

@saver
def new_user(chat_id):
    global users
    user = User(chat_id)
    users.append(user)

    return user

def new_dish(name, ingrdnts, chat_id):
    name = name.strip() # makes sure there are no whitespaces
    dish = Dish(name, ingrdnts)
    user = find_user(chat_id)
    if(user != None):
        user.add_dish(dish)
    else:
        new_user(chat_id)
        user.add_dish

def find_dish(name,chat_id):
    name = name.strip() # makes sure there are no whitespaces
    u = find_user(chat_id)
    if(u != None):
        for d in u.dishes:
            if(d.name.lower() == name.lower()):
                return d
    else:
        print("no user with that chat id")
    return None

def calculate_groceries(dishes):
    groceries = {}
    for dish in dishes:
        for ingr in dish.ingrdnts:
            if(ingr.name in groceries.keys()):
                print("found duplicat ingredient")
                groceries[ingr.name] = sum_of_quantities(groceries[ingr.name], ingr.quantity, ingr.units)
            else:
                groceries[ingr.name] = f"{ingr.quantity} {ingr.units}"
    
    return groceries
