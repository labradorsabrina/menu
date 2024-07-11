import os
import pandas as pd

file_path = "/Users/sabrina/Documents/Home/menu/Categories/category_mapping.txt"
folder_path = "/Users/sabrina/Documents/Home/menu/Recipes"

def read_category_mapping(file_path):
    df = pd.read_excel(file_path)
    category_mapping = {}
    for _, row in df.iterrows():
        ingredient = row['Product'].strip().upper()
        shopping_center = row['Place'].strip()
        location = row['Category'].strip()
        category_mapping[ingredient] = (shopping_center, location)
    return category_mapping

def read_recipes_from_folder(folder_path):
    recipes = {}
    for filename in os.listdir(folder_path):
        if filename.endswith(".txt"):
            recipe_name = filename[:-4].replace('_', ' ')
            with open(os.path.join(folder_path, filename), 'r') as file:
                lines = file.readlines()
            
            recipes[recipe_name] = {}
            reading_ingredients = False
            for line in lines:
                line = line.strip()
                if line.lower() == "ingredients:":
                    reading_ingredients = True
                elif line.lower() == "preparation:":
                    reading_ingredients = False
                elif reading_ingredients and line:
                    try:
                        ingredient, amount = line.split(':')
                        recipes[recipe_name][ingredient.strip().upper()] = amount.strip()
                    except ValueError:
                        print(f"Error parsing line in recipe file {filename}: {line}")
    return recipes

def choose_recipes(recipes):
    print("Available recipes:")
    for i, recipe in enumerate(recipes.keys(), 1):
        print(f"{i}. {recipe}")
    
    chosen_indices = input("\nEnter the numbers of the recipes you want to include, separated by commas: ")
    chosen_indices = [int(i.strip()) for i in chosen_indices.split(',')]
    
    chosen_recipes = {list(recipes.keys())[i-1]: recipes[list(recipes.keys())[i-1]] for i in chosen_indices}
    return chosen_recipes

def parse_amount(amount):
    try:
        number, unit = amount.split(maxsplit=1)
        return float(number), unit
    except ValueError:
        return 1, amount  # Assume 1 unit if parsing fails

def format_amount(total):
    if isinstance(total, float) and total.is_integer():
        total = int(total)
    return total

def generate_shopping_list(recipes, category_mapping):
    shopping_list = {}
    for recipe, ingredients in recipes.items():
        for ingredient, amount in ingredients.items():
            shopping_center, location = category_mapping.get(ingredient, ('Unknown', 'Unknown'))
            if shopping_center == 'Unknown':
                print(f"Warning: Ingredient '{ingredient.title()}' not found in category mapping.")
            key = (shopping_center, location, ingredient.title())
            quantity, unit = parse_amount(amount)
            if key in shopping_list:
                existing_quantity, existing_unit = shopping_list[key]
                if existing_unit == unit:
                    shopping_list[key] = (existing_quantity + quantity, unit)
                else:
                    print(f"Warning: Different units for the same ingredient '{ingredient.title()}'.")
                    shopping_list[key] = (shopping_list[key][0] + quantity, unit)
            else:
                shopping_list[key] = (quantity, unit)
    return shopping_list

def save_to_excel(shopping_list, file_path):
    data = []
    for key, (quantity, unit) in shopping_list.items():
        shopping_center, location, ingredient = key
        data.append({'Product': ingredient, 'Place': shopping_center, 'Category': location, 'Amount': format_amount(quantity), 'Unit': unit})
    
    df = pd.DataFrame(data)
    df.sort_values(by=['Place', 'Category', 'Product'], inplace=True)
    df.to_excel(file_path, index=False)

if __name__ == "__main__":
    category_file_path = os.path.join('categories', 'category_mapping.xlsx')
    folder_path = 'Recipes'
    
    category_mapping = read_category_mapping(category_file_path)
    recipes = read_recipes_from_folder(folder_path)
    chosen_recipes = choose_recipes(recipes)
    shopping_list = generate_shopping_list(chosen_recipes, category_mapping)
    save_to_excel(shopping_list, 'shopping_list.xlsx')
    print("The shopping list has been saved to 'shopping_list.xlsx'")
