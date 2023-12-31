import sqlite3
from sqlite3 import Error
import pandas as pd


class Database:
    def __init__(self, db_file):
        """
        Initialize database connection.
        Create tables if they do not exist.
        """
        self.conn = None
        try:
            self.conn = sqlite3.connect(db_file)
        except Error as e:
            print(e)

        if self.conn:
            self.create_tables()

    def create_tables(self):
        """ Create tables in the SQLite database"""
        # Ingredients table
        ingredients_table = """ CREATE TABLE IF NOT EXISTS ingredients (
                                    name text PRIMARY KEY,
                                    type text NOT NULL CHECK(type IN ('beef', 'pork', 'chicken', 'fish', 'vegetables', 'animal origin', 'legumes', 'cerial', 'fruit', 'other')),
                                    seasonality_start integer,
                                    seasonality_end integer,
                                    contains_gluten integer NOT NULL
                                ); """

        # Recipes table
        # Note: Many-to-many relationship and quantities will be handled separately
        recipes_table = """ CREATE TABLE IF NOT EXISTS recipes (
                                id integer PRIMARY KEY,
                                name text NOT NULL,
                                type text NOT NULL CHECK(type IN ('single dish', 'main dish', 'side dish')),
                                time_to_prepare integer NOT NULL,
                                portions integer NOT NULL,
                                preservation_days integer NOT NULL,
                                can_be_frozen integer,
                                score integer NOT NULL DEFAULT 0
                            ); """

        # Profiles table
        # Note: Many-to-many relationship with intolerances will be handled separately
        profiles_table = """ CREATE TABLE IF NOT EXISTS profiles (
                                name text PRIMARY KEY,
                                celiac integer NOT NULL
                            ); """

        # Recipe-Ingredients table (for many-to-many relationship and quantities)
        recipe_ingredients_table = """ CREATE TABLE IF NOT EXISTS recipe_ingredients (
                                                    recipe_id integer,
                                                    ingredient_name text,
                                                    quantity integer,
                                                    PRIMARY KEY(recipe_id, ingredient_name),
                                                    FOREIGN KEY(recipe_id) REFERENCES recipes(id),
                                                    FOREIGN KEY(ingredient_name) REFERENCES ingredients(name)
                                                ); """

        # Profile-Intolerances table (for many-to-many relationship)
        profile_intolerances_table = """ CREATE TABLE IF NOT EXISTS profile_intolerances (
                                                    profile_name text,
                                                    ingredient_name text,
                                                    PRIMARY KEY(profile_name, ingredient_name),
                                                    FOREIGN KEY(profile_name) REFERENCES profiles(name),
                                                    FOREIGN KEY(ingredient_name) REFERENCES ingredients(name)
                                                ); """
        # Storage table
        storage_table = """ CREATE TABLE IF NOT EXISTS storage (
                                ingredient_name text PRIMARY KEY,
                                quantity integer NOT NULL,
                                FOREIGN KEY(ingredient_name) REFERENCES ingredients(name)
                            ); """

        # Fridge table
        fridge_table = """ CREATE TABLE IF NOT EXISTS fridge (
                                recipe_id integer PRIMARY KEY,
                                portions integer NOT NULL,
                                FOREIGN KEY(recipe_id) REFERENCES recipes(id)
                            ); """
        # Freezer table
        freezer_table = """ CREATE TABLE IF NOT EXISTS freezer (
                                recipe_id integer PRIMARY KEY,
                                portions integer NOT NULL,
                                FOREIGN KEY(recipe_id) REFERENCES recipes(id)
                            ); """

        weekly_meal_plan_table = """ CREATE TABLE IF NOT EXISTS weekly_meal_plan (
                                        meal_id text PRIMARY KEY,
                                        day text NOT NULL CHECK(day IN ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')),
                                        meal text NOT NULL CHECK(meal IN ('lunch', 'dinner')),
                                        location text NOT NULL CHECK(location IN ('home', 'work')),
                                        recipe_id integer,
                                        FOREIGN KEY(recipe_id) REFERENCES recipes(id)
                                    ); """
        meal_profiles_table = """ CREATE TABLE IF NOT EXISTS meal_profiles (
                                    meal_id text,
                                    profile_name text,
                                    PRIMARY KEY(meal_id, profile_name),
                                    FOREIGN KEY(meal_id) REFERENCES weekly_meal_plan(meal_id),
                                    FOREIGN KEY(profile_name) REFERENCES profiles(name)
                                ); """
        meal_history_table = """ CREATE TABLE IF NOT EXISTS meal_history (
                                    id integer PRIMARY KEY,
                                    recipe_id integer NOT NULL,
                                    date text NOT NULL,
                                    in_season integer NOT NULL,
                                    score integer NOT NULL,
                                    accepted integer NOT NULL,
                                    FOREIGN KEY(recipe_id) REFERENCES recipes(id)
                                ); """

        try:
            self.conn.execute(ingredients_table)
            self.conn.execute(recipes_table)
            self.conn.execute(profiles_table)
            self.conn.execute(recipe_ingredients_table)
            self.conn.execute(profile_intolerances_table)
            self.conn.execute(recipe_ingredients_table)
            self.conn.execute(profile_intolerances_table)
            self.conn.execute(storage_table)
            self.conn.execute(fridge_table)
            self.conn.execute(freezer_table)
            self.conn.execute(weekly_meal_plan_table)
            self.conn.execute(meal_profiles_table)
            self.conn.execute(meal_history_table)

        except Error as e:
            print(e)

        # ... remaining methods ...

    def add_ingredient(self, ingredient):
        """
        Add a new ingredient to the database.
        If the ingredient exists, delete the existing one and insert the new one.
        """
        sql = ''' REPLACE INTO ingredients(name, type, seasonality_start, seasonality_end, contains_gluten)
                  VALUES(?,?,?,?,?) '''
        cur = self.conn.cursor()
        cur.execute(sql, ingredient)
        self.conn.commit()

    def delete_ingredient(self, name):
        """
        Delete an ingredient from the database by its name.
        """
        sql = 'DELETE FROM ingredients WHERE name=?'
        cur = self.conn.cursor()
        cur.execute(sql, (name,))
        self.conn.commit()

    def print_ingredient(self, name):
        """
        Print an ingredient's details by its name.
        """
        sql = 'SELECT * FROM ingredients WHERE name=?'
        cur = self.conn.cursor()
        cur.execute(sql, (name,))
        rows = cur.fetchall()

        for row in rows:
            print(f"Name: {row[0]}, Type: {row[1]}, Seasonality_start: {row[2]}, Seasonality_end:{row[3]}, Contains "
                  f"Gluten: {row[3]}")

        for row in rows:
            print(row)

    def print_all_ingredients(self):
        """
        Print all ingredients in the database.
        """
        sql = 'SELECT * FROM ingredients'
        cur = self.conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()

        for row in rows:
            print(f"Name: {row[0]}, Type: {row[1]}, Seasonality_start: {row[2]}, Seasonality_end:{row[3]}, Contains "
                  f"Gluten: {row[3]}")

    def add_recipe(self, recipe, ingredients):
        """
        Add a new recipe to the database.
        If the recipe exists, delete the existing one and insert the new one.
        `recipe` is a tuple containing the values for the fields of the recipe (id, name, type, time_to_prepare, portions, preservation_days, can_be_frozen, score)
        `ingredients` is a list of tuples, each containing the name of the ingredient and its quantity.
        """
        sql = ''' REPLACE INTO recipes(id, name, type, time_to_prepare, portions, preservation_days, can_be_frozen, score)
                  VALUES(?,?,?,?,?,?,?,?) '''
        cur = self.conn.cursor()
        cur.execute(sql, recipe)
        self.conn.commit()

        # Handle ingredients and their quantities
        for ingredient in ingredients:
            sql = ''' REPLACE INTO recipe_ingredients(recipe_id, ingredient_name, quantity)
                      VALUES(?,?,?) '''
            cur.execute(sql, (recipe[0], ingredient[0], ingredient[1]))
            self.conn.commit()

    def delete_recipe(self, id):
        """
        Delete a recipe from the database by its id.
        """
        sql = 'DELETE FROM recipes WHERE id=?'
        cur = self.conn.cursor()
        cur.execute(sql, (id,))
        self.conn.commit()

    def print_recipe(self, id):
        """
        Print a recipe's details by its id.
        """
        sql = 'SELECT * FROM recipes WHERE id=?'
        cur = self.conn.cursor()
        cur.execute(sql, (id,))
        rows = cur.fetchall()

        for row in rows:
            print(
                f"ID: {row[0]}, Name: {row[1]}, Type: {row[2]}, Time to prepare: {row[3]}, Portions: {row[4]}, "
                f"Preservation days: {row[5]}, Can be frozen: {row[6]}, Score: {row[7]}")

        # Print the ingredients associated with the recipe
        sql = 'SELECT ingredient_name, quantity FROM recipe_ingredients WHERE recipe_id=?'
        cur.execute(sql, (id,))
        rows = cur.fetchall()

        print("Ingredients:")
        for row in rows:
            print(f"Name: {row[0]}, Quantity: {row[1]}")

    def print_all_recipes(self):
        """
        Print all recipes in the database.
        """
        sql = 'SELECT * FROM recipes'
        cur = self.conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()

        for row in rows:
            print(
                f"ID: {row[0]}, Name: {row[1]}, Type: {row[2]}, Time to prepare: {row[3]}, Portions: {row[4]}, Preservation days: {row[5]}, Can be frozen: {row[6]}, Score: {row[7]}")

    def update_recipe_score(self, recipe_id, increment):
        """Update the score of a recipe"""
        if increment not in [-1, 1]:
            print("The score increment is wrong. It should be 1 or -1.")
            proceed = input("Do you want to modify the score anyway? (yes/no): ")
            if proceed.lower() != 'yes':
                return
        if self.conn is not None:
            try:
                # Create a cursor object
                cur = self.conn.cursor()
                # Execute the UPDATE statement
                cur.execute("UPDATE recipes SET score = score + ? WHERE id = ?", (increment, recipe_id,))
                # Commit the changes
                self.conn.commit()
            except Error as e:
                print(e)
        else:
            print("Error! Cannot create the database connection.")

    def get_recipe_ingredients(self, recipe_id):
        """
        Retrieves the ingredients and their quantities for a recipe by its id, along with additional information
        about each ingredient from the ingredients table.

        Parameters:
        recipe_id (int): The ID of the recipe.

        Returns:
        list: A list of dictionaries, each representing an ingredient and its details.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT ri.ingredient_name, ri.quantity, i.type, i.seasonality_start, i.seasonality_end, i.contains_gluten "
                "FROM recipe_ingredients AS ri "
                "JOIN ingredients AS i ON ri.ingredient_name = i.name "
                "WHERE ri.recipe_id = ?",
                (recipe_id,))
            ingredients = cursor.fetchall()
            return [{"name": name, "quantity": quantity, "type": type_, "seasonality_start": seasonality_start,
                     "seasonality_end": seasonality_end, "contains_gluten": contains_gluten} for
                    (name, quantity, type_, seasonality_start, seasonality_end, contains_gluten) in ingredients]
        except Error as e:
            print(e)

    def add_profile(self, profile, intolerances):
        """
        Add a new profile to the database.
        If the profile exists, delete the existing one and insert the new one.
        `profile` is a tuple containing the values for the fields of the profile (name, celiac)
        `intolerances` is a list of ingredient names.
        """
        sql = ''' REPLACE INTO profiles(name, celiac)
                  VALUES(?,?) '''
        cur = self.conn.cursor()
        cur.execute(sql, profile)
        self.conn.commit()

        # Handle intolerances
        for ingredient in intolerances:
            sql = ''' REPLACE INTO profile_intolerances(profile_name, ingredient_name)
                      VALUES(?,?) '''
            cur.execute(sql, (profile[0], ingredient))
            self.conn.commit()

    def delete_profile(self, name):
        """
        Delete a profile from the database by its name.
        """
        sql = 'DELETE FROM profiles WHERE name=?'
        cur = self.conn.cursor()
        cur.execute(sql, (name,))
        self.conn.commit()

    def print_profile(self, name):
        """
        Print a profile's details by its name.
        """
        sql = 'SELECT * FROM profiles WHERE name=?'
        cur = self.conn.cursor()
        cur.execute(sql, (name,))
        rows = cur.fetchall()

        for row in rows:
            print(f"Name: {row[0]}, Celiac: {row[1]}")

        # Print the intolerances associated with the profile
        sql = 'SELECT ingredient_name FROM profile_intolerances WHERE profile_name=?'
        cur.execute(sql, (name,))
        rows = cur.fetchall()

        print("Intolerances:")
        for row in rows:
            print(f"Ingredient: {row[0]}")

    def get_profile(self, name):
        """
        Print a profile's details by its name.
        """
        sql = 'SELECT * FROM profiles WHERE name=?'
        cur = self.conn.cursor()
        cur.execute(sql, (name,))
        rows = cur.fetchall()

        for row in rows:
            return row


    def print_all_profiles(self):
        """
        Print all profiles in the database.
        """
        sql = 'SELECT * FROM profiles'
        cur = self.conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()

        for row in rows:
            print(f"Name: {row[0]}, Celiac: {row[1]}")

    def get_all_profiles(self):
        """
        Retrieve all profiles in the database.

        Returns:
        list: A list of dictionaries, each representing a profile.
        """
        sql = 'SELECT * FROM profiles'
        cur = self.conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()

        profiles = []
        for row in rows:
            profiles.append({
                "name": row[0],
                "celiac": row[1]
            })

        return profiles

    def add_to_storage(self, ingredient, quantity):
        """
        Add an ingredient to storage or update the quantity if it already exists.
        """
        sql = 'REPLACE INTO storage(ingredient_name, quantity) VALUES(?, ?)'
        cur = self.conn.cursor()
        cur.execute(sql, (ingredient, quantity))
        self.conn.commit()

    def delete_from_storage(self, ingredient):
        """
        Delete an ingredient from storage.
        """
        sql = 'DELETE FROM storage WHERE ingredient_name=?'
        cur = self.conn.cursor()
        cur.execute(sql, (ingredient,))
        self.conn.commit()

    def modify_storage_quantity(self, ingredient, quantity):
        """
        Modify the quantity of an ingredient in storage.
        """
        sql = 'UPDATE storage SET quantity = ? WHERE ingredient_name = ?'
        cur = self.conn.cursor()
        cur.execute(sql, (quantity, ingredient))
        self.conn.commit()

    def add_to_fridge(self, recipe_id, portions):
        """
        Add a recipe to fridge or update the portions if it already exists.
        """
        sql = 'REPLACE INTO fridge(recipe_id, portions) VALUES(?, ?)'
        cur = self.conn.cursor()
        cur.execute(sql, (recipe_id, portions))
        self.conn.commit()

    def delete_from_fridge(self, recipe_id):
        """
        Delete a recipe from fridge.
        """
        sql = 'DELETE FROM fridge WHERE recipe_id=?'
        cur = self.conn.cursor()
        cur.execute(sql, (recipe_id,))
        self.conn.commit()

    def modify_fridge_portions(self, recipe_id, portions):
        """
        Modify the portions of a recipe in fridge.
        """
        sql = 'UPDATE fridge SET portions = ? WHERE recipe_id = ?'
        cur = self.conn.cursor()
        cur.execute(sql, (portions, recipe_id))
        self.conn.commit()

    def add_to_freezer(self, recipe_id, portions):
        """
        Add a recipe to freezer or update the portions if it already exists.
        """
        sql = 'REPLACE INTO freezer(recipe_id, portions) VALUES(?, ?)'
        cur = self.conn.cursor()
        cur.execute(sql, (recipe_id, portions))
        self.conn.commit()

    def delete_from_freezer(self, recipe_id):
        """
        Delete a recipe from freezer.
        """
        sql = 'DELETE FROM freezer WHERE recipe_id=?'
        cur = self.conn.cursor()
        cur.execute(sql, (recipe_id,))
        self.conn.commit()

    def modify_freezer_portions(self, recipe_id, portions):
        """
        Modify the portions of a recipe in freezer.
        """
        sql = 'UPDATE freezer SET portions = ? WHERE recipe_id = ?'
        cur = self.conn.cursor()
        cur.execute(sql, (portions, recipe_id))
        self.conn.commit()

    def print_storage(self):
        """
        Print all ingredients in storage.
        """
        sql = 'SELECT storage.ingredient_name, ingredients.type, storage.quantity FROM storage JOIN ingredients ON storage.ingredient_name = ingredients.name'
        cur = self.conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()

        print("Storage:")
        for row in rows:
            print(f"Ingredient: {row[0]}, Type: {row[1]}, Quantity: {row[2]}")

    def print_fridge(self):
        """
        Print all recipes in fridge.
        """
        sql = 'SELECT fridge.recipe_id, recipes.name, fridge.portions FROM fridge JOIN recipes ON fridge.recipe_id = recipes.id'
        cur = self.conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()

        print("Fridge:")
        for row in rows:
            print(f"Recipe ID: {row[0]}, Recipe: {row[1]}, Portions: {row[2]}")

    def print_freezer(self):
        """
        Print all recipes in freezer.
        """
        sql = 'SELECT freezer.recipe_id, recipes.name, freezer.portions FROM freezer JOIN recipes ON freezer.recipe_id = recipes.id'
        cur = self.conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()

        print("Freezer:")
        for row in rows:
            print(f"Recipe ID: {row[0]}, Recipe: {row[1]}, Portions: {row[2]}")

    def add_profile_to_meal(self, day, meal, profile_name):
        """
        Add a profile to a meal in the weekly meal plan.
        """
        meal_id = f"{day}_{meal}"
        sql = 'INSERT OR IGNORE INTO meal_profiles(meal_id, profile_name) VALUES(?,?)'
        cur = self.conn.cursor()
        cur.execute(sql, (meal_id, profile_name))
        self.conn.commit()

    def initialize_weekly_meal_plan(self):
        """
        Initialize the weekly meal plan by creating entries for each day of the week.
        Previous entries in the table are deleted.
        """
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        meals = ['lunch', 'dinner']

        cur = self.conn.cursor()

        # delete previous entries in the table
        cur.execute('DELETE FROM weekly_meal_plan')
        cur.execute('DELETE FROM meal_profiles')

        for day in days:
            for meal in meals:
                meal_id = f"{day}_{meal}"
                # create an entry for each day and meal, without assigning a profile or a recipe
                sql = 'INSERT OR IGNORE INTO weekly_meal_plan(meal_id, day, meal, location) VALUES(?,?,?,?)'
                cur.execute(sql, (meal_id, day, meal, 'home'))

        self.conn.commit()

    def print_weekly_meal_plan(self):
        """
        Print the weekly meal plan including the meals for each day of the week and the profiles that will be present at that meal.
        """
        sql = '''SELECT weekly_meal_plan.meal_id, day, meal, location, group_concat(profile_name), recipes.name 
                 FROM weekly_meal_plan 
                 LEFT JOIN meal_profiles ON weekly_meal_plan.meal_id = meal_profiles.meal_id
                 LEFT JOIN recipes ON weekly_meal_plan.recipe_id = recipes.id
                 GROUP BY weekly_meal_plan.meal_id ORDER BY day'''
        cur = self.conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()

        print(f"{'Day':<10} {'Meal':<10} {'Profiles':<15} {'Location':<10} {'Recipe':<10}")
        for row in rows:
            meal_id, day, meal, location, profiles, recipe = row
            print(
                f"{day:<10} {meal:<10} {profiles if profiles else '---':<15} {location:<10} {recipe if recipe else '---':<10}")

    def get_weekly_meal_plan(self):
        """
        Return the weekly meal plan including the meals for each day of the week and the profiles that will be present at that meal.
        """
        sql = 'SELECT weekly_meal_plan.meal_id, day, meal, location, group_concat(profile_name), recipe_id FROM weekly_meal_plan LEFT JOIN meal_profiles ON weekly_meal_plan.meal_id = meal_profiles.meal_id GROUP BY weekly_meal_plan.meal_id ORDER BY day'
        cur = self.conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()

        weekly_meal_plan = []

        for row in rows:
            meal_id, day, meal, location, profiles, recipe_id = row
            weekly_meal_plan.append({
                "day": day,
                "meal": meal,
                "profiles": profiles.split(',') if profiles else [],
                "location": location,
                "recipe_id": recipe_id
            })

        return weekly_meal_plan

    # Continue with other methods such as add_ingredient(), delete_ingredient(), print_ingredient(), etc.

    def add_recipe_to_meal(self, recipe_id, day, meal):
        """
        Add a recipe to a specific meal (lunch/dinner) of a specific day in the weekly meal plan.
        """
        sql = 'UPDATE weekly_meal_plan SET recipe_id = ? WHERE day = ? AND meal = ?'
        cur = self.conn.cursor()
        cur.execute(sql, (recipe_id, day, meal))
        self.conn.commit()

    def modify_meal_location(self, day, meal, location):
        """
        Modify the location of a specific meal (lunch/dinner) of a specific day in the weekly meal plan.
        """
        sql = 'UPDATE weekly_meal_plan SET location = ? WHERE day = ? AND meal = ?'
        cur = self.conn.cursor()
        cur.execute(sql, (location, day, meal))
        self.conn.commit()

    def add_to_meal_history(self, recipe_id, date, in_season, score, accepted):
        """
        Add an entry to meal history. If the total number of entries is more than 120, delete the oldest one.
        """
        sql = 'INSERT INTO meal_history(recipe_id, date, in_season, score, accepted) VALUES(?, ?, ?, ?, ?)'
        cur = self.conn.cursor()
        cur.execute(sql, (recipe_id, date, in_season, score, accepted))
        self.conn.commit()

        # Check the number of entries
        sql = 'SELECT COUNT(*) FROM meal_history'
        cur.execute(sql)
        count = cur.fetchone()[0]

        if count > 240:
            # Delete the oldest entry
            sql = 'DELETE FROM meal_history WHERE id = (SELECT MIN(id) FROM meal_history)'
            cur.execute(sql)
            self.conn.commit()

    def get_meal_history(self):
        """
        Return the entire meal history.
        """
        sql = 'SELECT * FROM meal_history'
        cur = self.conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()

        meal_history = []

        for row in rows:
            id, recipe_id, date, in_season, score, accepted = row
            meal_history.append({
                "id": id,
                "recipe_id": recipe_id,
                "date": date,
                "in_season": in_season,
                "score": score,
                "accepted": accepted
            })

        return meal_history

    def get_recipe_by_name(self, name):
        """
        Retrieves all information about a recipe based on its name.

        Parameters:
        name (str): The name of the recipe.

        Returns:
        dict: A dictionary containing all information about the recipe.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM Recipes WHERE name = ?", (name,))
            recipe = cursor.fetchone()
            return recipe
        except Error as e:
            print(e)

    def get_recipe_by_id(self, id):
        """
        Retrieves all information about a recipe based on its ID.

        Parameters:
        id (int): The ID of the recipe.

        Returns:
        dict: A dictionary containing all information about the recipe.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM Recipes WHERE id = ?", (id,))
            recipe = cursor.fetchone()
            return recipe
        except Error as e:
            print(e)

    def get_all_recipes(self):
        """
        Retrieves all recipes in the database.

        Returns:
        list: A list of dictionaries, each containing all information about a recipe.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM Recipes")
            recipes = cursor.fetchall()
            return recipes
        except Error as e:
            print(e)

    def get_fridge_contents(self):
        """
        Retrieves the contents of the fridge.

        Returns:
        list: A list of dictionaries, each representing a recipe and its quantity in the fridge.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM Fridge")
            fridge_contents = cursor.fetchall()
            return fridge_contents
        except Error as e:
            print(e)

    def get_freezer_contents(self):
        """
        Retrieves the contents of the freezer.

        Returns:
        list: A list of dictionaries, each representing a recipe and its quantity in the freezer.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM Freezer")
            freezer_contents = cursor.fetchall()
            return freezer_contents
        except Error as e:
            print(e)

    def get_all_ingredients(self):
        """
        Retrieves all ingredients in the database.

        Returns:
        list: A list of tuples, each containing all information about an ingredient.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM ingredients")
            ingredients = cursor.fetchall()
            return ingredients
        except Error as e:
            print(e)

    def get_ingredient(self, ingredient_name):
        """
        Retrieves all information of an ingredient based on its name.

        Parameters:
        ingredient_name (str): The name of the ingredient.

        Returns:
        dict: A dictionary containing all information about the ingredient.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM ingredients WHERE name = ?", (ingredient_name,))
            ingredient_info = cursor.fetchone()

            if ingredient_info is not None:
                return {
                    "name": ingredient_info[0],
                    "type": ingredient_info[1],
                    "seasonality_start": ingredient_info[2],
                    "seasonality_end": ingredient_info[3],
                    "contains_gluten": ingredient_info[4]
                }
            else:
                print(f"No ingredient with name {ingredient_name} found in the database.")
                return None

        except Error as e:
            print(e)

    def load_data_from_csv(self, csv_file, table_name):
        # Read the CSV file into a DataFrame
        df = pd.read_csv(csv_file)

        # Convert the DataFrame into a list of tuples
        data_to_insert = [tuple(row) for row in df.values]

        # Get the column names from the DataFrame
        column_names = ','.join(df.columns)

        # Prepare the placeholders for the values
        placeholders = ','.join(['?'] * len(df.columns))

        # Prepare the SQL statement
        sql = f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})"

        # Use a cursor to interact with the database
        cursor = self.conn.cursor()

        # Iterate over the data to insert
        for row in data_to_insert:
            try:
                # Execute the SQL statement
                cursor.execute(sql, row)

            except sqlite3.IntegrityError as e:
                # This catches violations of unique constraints and foreign key constraints
                print(f"Error inserting {row} into {table_name}: {e}")

        # Commit the changes
        self.conn.commit()

        # Close the cursor
        cursor.close()

    # Usage:
    # conn = sqlite3.connect('your_database.db')
    # load_data_from_csv(conn, 'ingredients.csv', 'ingredients')


def main():
    # Create a Database object
    db = Database('test.db')

    while True:
        # Ask the user for the name of the CSV file
        csv_file = input("Enter the name of the CSV file (or 'quit' to stop): ")

        if csv_file.lower() == 'quit':
            break

        # Ask the user for the name of the table
        table_name = input("Enter the name of the table: ")

        # Load the data from the CSV file into the table
        db.load_data_from_csv(csv_file, table_name)

    print(db.get_recipe_ingredients(1))

if __name__ == "__main__":
    main()
