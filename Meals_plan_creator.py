from datetime import date
from datetime import datetime


class Meals_plan_creator:

    def __init__(self, db, prediction_list):
        self.db = db
        self.predictions = prediction_list.copy()

    def is_participant_in_profiles(self, participant, profiles):
        for profile in profiles:
            if profile['name'].lower() == participant.lower():
                return True
        return False

    def create_temporary_meal_plan(self, db):
        """Create a temporary meal plan with user interaction."""

        # Initialize a temporary meal plan
        temp_meal_plan = {
            "Monday": {"lunch": {"participants": [], "location": ""}, "dinner": {"participants": [], "location": ""}},
            "Tuesday": {"lunch": {"participants": [], "location": ""}, "dinner": {"participants": [], "location": ""}},
            "Wednesday": {"lunch": {"participants": [], "location": ""},
                          "dinner": {"participants": [], "location": ""}},
            "Thursday": {"lunch": {"participants": [], "location": ""}, "dinner": {"participants": [], "location": ""}},
            "Friday": {"lunch": {"participants": [], "location": ""}, "dinner": {"participants": [], "location": ""}},
            "Saturday": {"lunch": {"participants": [], "location": ""}, "dinner": {"participants": [], "location": ""}},
            "Sunday": {"lunch": {"participants": [], "location": ""}, "dinner": {"participants": [], "location": ""}}
        }

        # Get all profiles
        profiles = db.get_all_profiles()

        profiles_string = ""

        if profiles is None:
            profiles = []

        for profile in profiles:
            profiles_string = profiles_string + "   " + profile['name']

        for day, meals in temp_meal_plan.items():
            print(f"\nDay: {day}")
            for meal, info in meals.items():
                print(f"\nMeal: {meal}")

                # Set participants
                while True:
                    print("list of partecipants", profiles_string)
                    participant = input("Enter the name of a participant or 'done' to finish:")
                    if participant.lower() == 'done':
                        break
                    elif self.is_participant_in_profiles(participant, profiles):
                        info["participants"].append(participant)
                    else:
                        print("This profile does not exist. Please try again.")

                # Set location
                while True:
                    location = input("Enter the location ('home' or 'work'): ")
                    if location.lower() in ['home', 'work']:
                        info["location"] = location.lower()
                        break
                    else:
                        print("Invalid location. Please enter 'home' or 'work'.")

                # Confirm settings
                while True:
                    confirm = input("Do you want to confirm these settings? (yes/no): ")
                    if confirm.lower() == 'yes':
                        print("Settings confirmed.")
                        break
                    elif confirm.lower() == 'no':
                        print("Please set the participants and location again.")
                        break
                    else:
                        print("Invalid option. Please enter 'yes' or 'no'.")

        return temp_meal_plan

    def single_meal(self):
        """
        method that produces a single meal, it keeps offering options until the user accept one, it uses the list of
        recipies with their probability of being chosen. It ads the chosen recipies to the history
        :return:
        """
        # Get all profiles
        profiles = self.db.get_all_profiles()
        celiac = False
        profiles_string = ""
        participants = []
        if profiles is None:
            profiles = []

        # sets up a string of profile in order to print the m formatted
        for profile in profiles:
            profiles_string = profiles_string + "   " + profile['name']

        # prints all the profile present in the database asks to insert a partecipant if the user insert "done"
        # in stops
        while True:
            print("list of partecipants", profiles_string)
            participant = input("Enter the name of a participant or 'done' to finish:")
            if participant.lower() == 'done':
                break
            elif self.is_participant_in_profiles(participant, profiles):
                participants.append(participant)
            else:
                print("This profile does not exist. Please try again.")

        # Checks that the list of partecipants in not empty and then asks to the user to verify the input
        if participants == None:
            print("Please reinsert the partecipants")
            return self.single_meal()
        participants_info = []
        print("this are the partecipants:")
        for participant in participants:
            participant_info = self.db.get_profile(participant)
            print(participant_info)
            participants_info.append(participant_info)

        if verified_input("Do you confirm? [y/n]") == 'n':
            print("please reinsert the partecipants")
            return self.single_meal()

        "checks if any participant has celiac disease"
        for participant in participants_info:
            if participant is None:
                participants_info.remove(participant)
            elif participant[1] == 1:
                celiac = True
        # sorts the predictions dictionary based on the probability of each recipe to be chosen
        sorted_predictions = sorted(self.predictions, key=lambda x: x['probability'], reverse=True)

        # creates a list containing main dishes in order of probability, main dishes are both main and single dishes
        main_dishes = []
        sides = []

        # removes all the dishes that contain gluten in case a celiac is participating to the meal. At the same time fills
        # the list of main dishes and the list of sides
        for recipe in sorted_predictions:
            removed = False
            ingredients = self.db.get_recipe_ingredients(recipe["id"])
            if celiac:
                for ingredient in ingredients:
                    if ingredient['contains_gluten'] == 1:
                        sorted_predictions.remove(recipe)
                        removed = True
                        break
            if removed == False:
                recipe_info = self.db.get_recipe_by_id(recipe['id'])
                if recipe_info[2] == 'main dish' or recipe_info[2] == 'single dish':
                    main_dishes.append(recipe_info)
                else:
                    sides.append(recipe_info)

        # starts from the most likely to the less likely to ask if each main dish is accepted
        confirmed_dish = None
        for main_dish in main_dishes:
            if verified_input(f"the suggestion is {main_dish} is it ok? ") == 'y':
                confirmed_dish = main_dish
                self.update_database(main_dish[0], True)
                break
            else:
                self.update_database(main_dish[0], False)

        # if the accepted dish is a "main dish" it asks if the user wants sides if it is a single dis it doesn't
        confirmed_sides = []
        if confirmed_dish[2] == 'main dish':
            if verified_input("Do you want also sides?") == 'y':
                for side_dish in sides:
                    answer = verified_input(f"the suggestion is {side_dish[1]} is it ok?")
                    if answer == 'y':
                        confirmed_sides.append(side_dish)
                        self.update_database(side_dish[0], True)
                    else:
                        self.update_database(side_dish[0], False)
                        if verified_input('do you want other sides?') == 'n':
                            break

        if len(sides) > 0:
            print(f"The selected meal is composed by:\n Main Dish\n\n {confirmed_dish[1]}\n Sides\n")

            for side in confirmed_sides:
                print(side[1])




    def update_database(self, recipe_id, accepted):
        recipe = self.db.get_recipe_by_id(recipe_id)

        if accepted:
            self.db.update_recipe_score(recipe_id, +1)
            self.db.add_to_meal_history(recipe_id, date.today().strftime("%Y-%m-%d"), check_season(self.db, recipe_id), recipe[7], 1)
        else:
            self.db.update_recipe_score(recipe_id, -1)
            self.db.add_to_meal_history(recipe_id, date.today().strftime("%Y-%m-%d"), check_season(self.db, recipe_id),
                                        recipe[7], 0)
        print(self.db.get_meal_history())
        return


def check_season(db, recipe_id):
    recipe_ingredients = db.get_recipe_ingredients(recipe_id)

    current_month = datetime.now().month

    for ingredient in recipe_ingredients:
        if ingredient['seasonality_start'] >= current_month >= ingredient['seasonality_end']:
            return 0

    return 1


def verified_input(question):
    """
    function that checks if the answer is 'y' or 'n' to avoid confusion and keep the data clean
    :param question: String that contains the question
    :return: the answer as 'y' or  'n'
    """
    answer = 'n'
    while answer != 'y':
        answer = input(question).lower()
        print(answer)
        if answer == 'n':
            break

    return answer
