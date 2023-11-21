from Database import Database
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix
from Meals_plan_creator import Meals_plan_creator


# Here is a Python function which will interactively ask the user for the details needed to add a recipe.

def add_recipe_interactive(db):
    name = input("Enter the name of the recipe: ")
    method = input("Enter the method of preparation of the recipe: ")
    servings = input("Enter the number of servings of the recipe: ")

    # Initialize the ingredients list
    ingredients = []

    while True:
        ingredient_name = input("Enter the name of an ingredient (or 'done' to finish): ")
        if ingredient_name.lower() == 'done':
            break
        ingredient_qty = input(f"Enter the quantity of {ingredient_name}: ")
        ingredients.append((ingredient_name, ingredient_qty))

    # Use the add_recipe method from the Database class
    db.add_recipe((id, name, method, servings), ingredients)


# To use this function, you would do something like this (assuming db is your Database instance):
# add_recipe_interactive(db)


def delete_recipe_interactive(db):
    """
    Ask the user for the ID of the recipe they want to delete, and then delete it from the database.
    """
    recipe_id = input("Enter the ID of the recipe you want to delete: ")

    # Check if the recipe exists in the database
    recipe = db.get_recipe_by_id(recipe_id)
    if recipe is None:
        print(f"No recipe with ID {recipe_id} found.")
    else:
        db.delete_recipe(recipe_id)
        print(f"Recipe with ID {recipe_id} has been deleted.")


def add_profile_interactive(db):
    """
    Interactive function to add a profile to the database.
    """
    print("Adding a new profile.")
    name = input("Enter the name of the profile: ")
    celiac = input("Is the person celiac? Enter 1 for Yes and 0 for No: ")

    intolerances = []
    while True:
        intolerance = input("Enter an ingredient that the person is intolerant to (or 'done' if there are no more): ")
        if intolerance.lower() == 'done':
            break
        intolerances.append(intolerance)

    # Create the profile tuple
    profile = (name, int(celiac))

    # Add the profile to the database
    db.add_profile(profile, intolerances)


def delete_profile_interactive(db):
    """
    Interactive function to delete a profile from the database.
    """
    print("Deleting a profile.")
    name = input("Enter the name of the profile to delete: ")

    # Delete the profile from the database
    db.delete_profile(name)


def add_to_fridge_interactive(db):
    print("Add a recipe to the fridge:")
    recipe_id = input("Please enter the ID of the recipe you want to add: ")
    portions = input("Please enter the number of portions: ")

    # Convert to appropriate data types
    recipe_id = int(recipe_id)
    portions = int(portions)

    db.add_to_fridge(recipe_id, portions)
    print(f"Recipe {recipe_id} with {portions} portions has been added to the fridge.")


def add_to_freezer_interactive(db):
    print("Add a recipe to the freezer:")
    recipe_id = input("Please enter the ID of the recipe you want to add: ")
    portions = input("Please enter the number of portions: ")

    # Convert to appropriate data types
    recipe_id = int(recipe_id)
    portions = int(portions)

    db.add_to_freezer(recipe_id, portions)
    print(f"Recipe {recipe_id} with {portions} portions has been added to the freezer.")


def print_weekly_plan(db):
    """Print the weekly meal plan."""
    weekly_plan = db.get_weekly_meal_plan()
    for meal in weekly_plan:
        day = meal['day']
        meal_time = meal['meal']
        location = meal['location']
        profiles = ', '.join(meal['profiles'])
        recipe_id = meal['recipe_id'] if meal['recipe_id'] is not None else '---'
        print(f"Day: {day}, Meal: {meal_time}, Location: {location}, Profiles: {profiles}, Recipe ID: {recipe_id}")


def replace_none_values_with_average(dataset):
    # Calculate the sum and count of non-None time_from_last_eaten values
    total_time = 0
    count = 0
    for data in dataset:
        if data['time_from_last_eaten'] is not None:
            total_time += data['time_from_last_eaten']
            count += 1

    # Calculate the average time from last eaten
    average_time = total_time / count if count > 0 else None

    # Replace None values with the average
    for data in dataset:
        if data['time_from_last_eaten'] is None:
            data['time_from_last_eaten'] = average_time

    return dataset


def check_season(db, recipe_id):
    recipe_ingredients = db.get_recipe_ingredients(recipe_id)

    current_month = datetime.now().month

    for ingredient in recipe_ingredients:
        if ingredient['seasonality_start'] >= current_month and ingredient['seasonality_end'] <= current_month:
            return 0

    return 1


def create_dataset(db):
    # Get all recipes from the database
    all_recipes = db.get_all_recipes()

    # Transform it into a dictionary for easier access
    # Assuming the structure of each recipe is as follows:
    # (id, name, type, time_to_prepare, portions, preservation_days, can_be_frozen, score)
    recipes_dict = {recipe[0]: {"name": recipe[1], "type": recipe[2], "time_to_prepare": recipe[3],
                                "portions": recipe[4], "preservation_days": recipe[5],
                                "can_be_frozen": recipe[6], "score": recipe[7]} for recipe in all_recipes}


    # Get the meal history
    meal_history = db.get_meal_history()
    # Sort meal history by date
    meal_history.sort(key=lambda x: datetime.strptime(x['date'], '%Y-%m-%d'), reverse=True)

    # Initialize the last eaten dates dictionary
    last_eaten_dates = {}

    # Initialize the dataset
    dataset = []

    for meal in meal_history:
        # Get the corresponding recipe
        recipe = recipes_dict[meal['recipe_id']]

        # Calculate time from last eaten
        current_date = datetime.strptime(meal['date'], '%Y-%m-%d')

        # for each recipe checks when it was eaten the previous time
        time_from_last_eaten = 0

        # print("meal check")
        for old_meal in meal_history:
            last_eaten_date = datetime.strptime(old_meal['date'], '%Y-%m-%d')
            if meal['recipe_id'] == old_meal['recipe_id'] and old_meal[
                'accepted'] == 1 and last_eaten_date <= current_date:
                time_from_last_eaten = (current_date - last_eaten_date).days
                break
            else:
                time_from_last_eaten = 0

        # Create the data row
        data_row = {
            'time_to_prepare': recipe['time_to_prepare'],
            'portions': recipe['portions'],
            'preservation_days': recipe['preservation_days'],
            'can_be_frozen': recipe['can_be_frozen'],
            'time_from_last_eaten': time_from_last_eaten,
            'score': meal['score'],
            'in_season': meal['in_season'],
            'accepted': meal['accepted']
        }

        # Add the data row to the dataset
        dataset.append(data_row)
    dataset = replace_none_values_with_average(dataset)
    print(dataset)
    return dataset


def train_logistic_regression_check(dataset):
    # Convert the dataset into features and labels
    X = [[entry['time_to_prepare'], entry['portions'], entry['preservation_days'], entry['can_be_frozen'],
          entry['time_from_last_eaten'], entry['in_season'], entry['score']] for entry in dataset]
    y = [entry['accepted'] for entry in dataset]

    # Split the dataset into a training set and a test set
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Create a Logistic Regression model and train it on the training set
    model = LogisticRegression()
    model.fit(X_train, y_train)

    # Use the model to make predictions on the test set
    y_pred = model.predict(X_test)

    # Calculate the accuracy of the model
    accuracy = accuracy_score(y_test, y_pred)

    # Calculate the confusion matrix
    confusion_mat = confusion_matrix(y_test, y_pred)

    return model, accuracy, confusion_mat


def create_predicion_list(db, model):
    all_recipes = db.get_all_recipes()

    # Transform it into a dictionary for easier access
    # Assuming the structure of each recipe is as follows:
    # (id, name, type, time_to_prepare, portions, preservation_days, can_be_frozen, score)
    recipes_dict = {recipe[0]: {"recipe_id": recipe[0], "name": recipe[1], "type": recipe[2], "time_to_prepare": recipe[3],
                    "portions": recipe[4], "preservation_days": recipe[5],
                    "can_be_frozen": recipe[6], "score": recipe[7]} for recipe in all_recipes}

    # Get the meal history
    meal_history = db.get_meal_history()
    # Sort meal history by date
    meal_history.sort(key=lambda x: datetime.strptime(x['date'], '%Y-%m-%d'), reverse=True)

    # Calculate time from last eaten
    current_date = datetime.now()

    # Initialize the dataset
    dataset = []

    for recipe_id in recipes_dict:
        recipe = recipes_dict[recipe_id]
        time_from_last_eaten = None
        for meal in meal_history:
            if meal['recipe_id'] == recipe['recipe_id']:
                time_from_last_eaten = (current_date - datetime.strptime(meal['date'], '%Y-%m-%d')).days
                break
        in_season = check_season(db, recipe['recipe_id'])
        data_row = {
            'recipe_id': recipe["recipe_id"],
            'time_to_prepare': recipe['time_to_prepare'],
            'portions': recipe['portions'],
            'preservation_days': recipe['preservation_days'],
            'can_be_frozen': recipe['can_be_frozen'],
            'time_from_last_eaten': time_from_last_eaten,
            'score': meal['score'],
            'in_season': in_season
        }

        # Add the data row to the dataset
        dataset.append(data_row)

    dataset = replace_none_values_with_average(dataset)
    list_predictions = []
    for entry in dataset:
        X = [entry['time_to_prepare'], entry['portions'], entry['preservation_days'], entry['can_be_frozen'],
             entry['time_from_last_eaten'], entry['in_season'], entry['score']]
        probabilities = model.predict_proba([X])
        element = {
            "id": entry['recipe_id'],
            "probability": probabilities[0][1]}
        list_predictions.append(element)

    print(dataset)
    print(list_predictions)

    return list_predictions

def train_logistic_regression(dataset, db):
    # Convert the dataset into features and labels
    X = [[entry['time_to_prepare'], entry['portions'], entry['preservation_days'], entry['can_be_frozen'],
          entry['time_from_last_eaten'], entry['in_season'], entry['score']] for entry in dataset]
    y = [entry['accepted'] for entry in dataset]

    # Split the dataset into a training set and a test set
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.01, random_state=42)

    # Create a Logistic Regression model and train it on the training set
    model = LogisticRegression()
    model.fit(X_train, y_train)

    # Use the model to make probability predictions on the test set
    return create_predicion_list(db, model)


def print_menu():
    print("\nMeal Planner Menu:")
    print("1. Add an ingredient")
    print("2. Delete an ingredient")
    print("3. View all ingredients")
    print("4. Add a recipe")
    print("5. Delete a recipe")
    print("6. View all recipes")
    print("7. Add a profile")
    print("8. Delete a profile")
    print("9. View all profiles")
    print("10. Add ingredient to storage")
    print("11. View storage")
    print("12. Add recipe to fridge")
    print("13. View fridge")
    print("14. Add recipe to freezer")
    print("15. View freezer")
    print("16. Print weekly plan")
    print("17. Create weekly plan")
    print("16. Exit")


def main():
    # Get the database name from the user
    db_name = input("Enter the name of the database: ")

    # Create a Database object
    db = Database(db_name + '.db')

    while True:
        print_menu()
        choice = input("Enter your choice: ")

        if choice == '1':
            name = input("Enter the name of the ingredient: ")
            type = input("Enter the type of the ingredient\n(berween 'beef', 'pork', 'chicken', 'fish', 'vegetables', "
                         "'animal origin', 'legumes', 'cerial', 'fruit', 'other'): ")
            seasonality_start = input("Enter the seasonality of the ingredient: ")
            seasonality_end = input("Enter the seasonality of the ingredient: ")
            contains_gluten = int(input("Does the ingredient contain gluten? Enter 1 for yes, 0 for no: "))
            db.add_ingredient((name, type, seasonality_start, seasonality_end, contains_gluten))
        elif choice == '2':
            name = input("Enter the name of the ingredient to delete: ")
            db.delete_ingredient(name)
        elif choice == '3':
            db.print_all_ingredients()
        elif choice == '4':
            add_recipe_interactive(db)
        elif choice == '5':
            delete_recipe_interactive(db)
        elif choice == '6':
            db.print_all_recipes()
        elif choice == '7':
            add_profile_interactive(db)
        elif choice == '8':
            delete_profile_interactive(db)
            # delete_profile method implementation
        elif choice == '9':
            db.print_all_profiles()
        # elif choice == '10':
        # add_to_storage method implementation
        elif choice == '11':
            db.print_storage()
        elif choice == '12':
            add_to_fridge_interactive(db)
            # add_to_fridge method implementation
        elif choice == '13':
            db.print_fridge()
        elif choice == '14':
            add_to_freezer_interactive(db)
            # add_to_freezer method implementation
            # 1elif choice == '15':
            db.print_freezer(db)
        elif choice == '16':
            db.print_weekly_meal_plan()
        elif choice == '17':
            dataset = create_dataset(db)
            list_of_predictions = train_logistic_regression(dataset, db)
            planner = Meals_plan_creator(db, list_of_predictions)
            planner.single_meal()


        # create_temporary_meal_plan(db)

        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
