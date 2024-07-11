import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QListWidget, QVBoxLayout, QMessageBox, QComboBox, QTextEdit, QScrollArea, QFileDialog
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QPixmap
from PyQt5.QtCore import Qt
import pandas as pd
import os
import requests
from io import BytesIO

class SearchableComboBox(QWidget):
    def __init__(self, parent=None):
        super(SearchableComboBox, self).__init__(parent)
        self.combo_box = QComboBox()
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search product...")
        self.search_bar.textChanged.connect(self.filter_products)
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.search_bar)
        self.layout.addWidget(self.combo_box)
        self.setLayout(self.layout)
        
        self.products = []

    def filter_products(self, text):
        text = text.strip().upper()
        self.combo_box.clear()
        self.combo_box.addItem("Select a product")

        current_category = None
        for product, place, category in self.products:
            if text in product:
                if category != current_category:
                    item = QStandardItem(category)
                    item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
                    self.combo_box.model().appendRow(item)
                    current_category = category
                self.combo_box.addItem(f"    {product.title()}")

    def add_items(self, items):
        self.products = items
        self.filter_products("")  # Initially populate the combo box

class PlainTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

    def insertFromMimeData(self, source):
        self.insertPlainText(source.text())

class RecipeApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.load_category_mapping()

    def initUI(self):
        self.setWindowTitle('Recipe Entry')

        # Create UI elements
        self.lbl_recipe_name = QLabel('Recipe Name:')
        self.recipe_name_entry = QLineEdit()

        self.lbl_product = QLabel('Product:')
        self.product_combobox = SearchableComboBox()

        self.update_products_button = QPushButton('Update Products')
        self.update_products_button.clicked.connect(self.update_products)

        self.lbl_unit = QLabel('Unit:')
        self.unit_combobox = QComboBox()
        self.unit_combobox.addItems([
            "Select a unit", "tsp", "tbsp", "cup", "ml", "l", "g", "kg", "oz", "lb", "clove", "head", "piece", "to taste", "leaves", "bag", "can"
        ])

        self.lbl_amount = QLabel('Amount:')
        self.amount_entry = QLineEdit()

        self.ingredients_list = QListWidget()
        self.ingredients_list.setMinimumHeight(200)  # Set minimum height for ingredients list

        self.lbl_preparation = QLabel('Preparation:')
        self.preparation_text = PlainTextEdit()
        self.preparation_text.setMinimumHeight(200)  # Set minimum height for preparation text

        self.lbl_url = QLabel('URL:')
        self.url_entry = QLineEdit()

        self.lbl_image_url = QLabel('Image URL:')
        self.image_url_entry = QLineEdit()
        self.load_image_button = QPushButton('Load Image')
        self.load_image_button.clicked.connect(self.load_image)
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)

        self.add_button = QPushButton('Add Ingredient', self)
        self.add_button.clicked.connect(self.add_ingredient)

        self.edit_button = QPushButton('Edit Ingredient', self)
        self.edit_button.clicked.connect(self.edit_ingredient)

        self.delete_button = QPushButton('Delete Ingredient', self)
        self.delete_button.clicked.connect(self.delete_ingredient)

        self.save_button = QPushButton('Save Recipe', self)
        self.save_button.clicked.connect(self.save_recipe)

        self.load_button = QPushButton('Load Recipe', self)
        self.load_button.clicked.connect(self.load_recipe)

        # Layouts
        vbox = QVBoxLayout()
        vbox.addWidget(self.lbl_recipe_name)
        vbox.addWidget(self.recipe_name_entry)
        vbox.addWidget(self.update_products_button)
        vbox.addWidget(self.lbl_product)
        vbox.addWidget(self.product_combobox)
        vbox.addWidget(self.lbl_unit)
        vbox.addWidget(self.unit_combobox)
        vbox.addWidget(self.lbl_amount)
        vbox.addWidget(self.amount_entry)
        vbox.addWidget(self.add_button)
        vbox.addWidget(self.edit_button)
        vbox.addWidget(self.delete_button)
        vbox.addWidget(self.ingredients_list)
        vbox.addWidget(self.lbl_preparation)
        vbox.addWidget(self.preparation_text)
        vbox.addWidget(self.lbl_url)
        vbox.addWidget(self.url_entry)
        vbox.addWidget(self.lbl_image_url)
        vbox.addWidget(self.image_url_entry)
        vbox.addWidget(self.load_image_button)
        vbox.addWidget(self.image_label)
        vbox.addWidget(self.save_button)
        vbox.addWidget(self.load_button)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_content.setLayout(vbox)
        scroll_area.setWidget(scroll_content)

        main_layout = QVBoxLayout()
        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)

        # Show the window in full screen
        self.showFullScreen()

    def load_category_mapping(self):
        category_file_path = os.path.join('categories', 'category_mapping.xlsx')
        if os.path.exists(category_file_path):
            df = pd.read_excel(category_file_path)
            self.category_mapping = {row['Product'].strip().upper(): (row['Place'].strip(), row['Category'].strip()) for _, row in df.iterrows()}
            
            # Categories to exclude
            excluded_categories = {"Personal Care"}

            # Organize products by category and then by name, excluding certain categories
            self.products = sorted(
                [(product, place, category) for product, (place, category) in self.category_mapping.items() if category not in excluded_categories],
                key=lambda item: (item[2], item[0])
            )
            
            self.product_combobox.add_items(self.products)
        else:
            self.category_mapping = {}

    def update_products(self):
        self.load_category_mapping()

    def add_ingredient(self):
        product_info = self.product_combobox.combo_box.currentText().strip()
        product = product_info.strip().upper()
        if product.startswith("    "):
            product = product[4:]
        amount = self.amount_entry.text().strip()
        unit = self.unit_combobox.currentText().strip()

        if product_info == "Select a product" or not amount or unit == "Select a unit":
            QMessageBox.critical(self, 'Input Error', 'Please fill all fields and select a product and unit')
            return

        if product not in self.category_mapping:
            QMessageBox.critical(self, 'Validation Error', f"Product '{product}' is not in the category mapping")
            return

        self.ingredients_list.addItem(f"{product}: {amount} {unit}")
        
        # Reset product and unit fields
        self.product_combobox.combo_box.setCurrentIndex(0)
        self.unit_combobox.setCurrentIndex(0)
        self.amount_entry.clear()
        self.product_combobox.search_bar.clear()

    def edit_ingredient(self):
        current_item = self.ingredients_list.currentItem()
        if current_item:
            product_info, amount_unit = current_item.text().split(':')
            amount_unit = amount_unit.strip().split(' ')
            amount = amount_unit[0]
            unit = amount_unit[1] if len(amount_unit) > 1 else ""
            self.product_combobox.combo_box.setCurrentText(f"    {product_info.strip().title()}")
            self.amount_entry.setText(amount)
            self.unit_combobox.setCurrentText(unit)
            self.ingredients_list.takeItem(self.ingredients_list.row(current_item))

    def delete_ingredient(self):
        current_item = self.ingredients_list.currentItem()
        if current_item:
            self.ingredients_list.takeItem(self.ingredients_list.row(current_item))

    def load_image(self):
        image_url = self.image_url_entry.text().strip()
        if not image_url:
            QMessageBox.critical(self, 'Input Error', 'Please enter the Image URL')
            return
        
        # Check if the URL ends with a valid image extension
        if not any(image_url.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif']):
            QMessageBox.critical(self, 'Input Error', 'Please enter a direct link to an image (ending with .jpg, .jpeg, .png, .gif)')
            return

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }

        try:
            response = requests.get(image_url, headers=headers)
            response.raise_for_status()
            image = QPixmap()
            image.loadFromData(BytesIO(response.content).read())
            scaled_image = image.scaledToHeight(300, Qt.SmoothTransformation)
            self.image_label.setPixmap(scaled_image)
        except Exception as e:
            QMessageBox.critical(self, 'Error', f"Failed to load image: {str(e)}")

    def save_recipe(self):
        recipe_name = self.recipe_name_entry.text().strip()
        if not recipe_name:
            QMessageBox.critical(self, 'Input Error', 'Please enter the recipe name')
            return

        ingredients = [self.ingredients_list.item(i).text() for i in range(self.ingredients_list.count())]
        if not ingredients:
            QMessageBox.critical(self, 'Input Error', 'Please add at least one ingredient')
            return

        preparation = self.preparation_text.toPlainText().strip()
        if not preparation:
            QMessageBox.critical(self, 'Input Error', 'Please enter the preparation steps')
            return

        url = self.url_entry.text().strip()
        if not url:
            QMessageBox.critical(self, 'Input Error', 'Please enter the URL')
            return

        image_url = self.image_url_entry.text().strip()
        if not image_url:
            QMessageBox.critical(self, 'Input Error', 'Please enter the Image URL')
            return

        recipe_folder = 'Recipes'
        os.makedirs(recipe_folder, exist_ok=True)
        recipe_file_path = os.path.join(recipe_folder, f"{recipe_name.replace(' ', '_')}.txt")

        with open(recipe_file_path, 'w') as file:
            file.write("Ingredients:\n")
            for ingredient in ingredients:
                file.write(f"{ingredient}\n")
            file.write("\nPreparation:\n")
            file.write(preparation)
            file.write("\nURL:\n")
            file.write(url)
            file.write("\nImage URL:\n")
            file.write(image_url)

        QMessageBox.information(self, 'Success', f"Recipe '{recipe_name}' saved successfully")
        self.clear_entries()

    def load_recipe(self):
        options = QFileDialog.Options()
        recipe_folder = os.path.join(os.getcwd(), 'Recipes')  # Set default folder to "Recipes" directory
        file_name, _ = QFileDialog.getOpenFileName(self, "Load Recipe", recipe_folder, "Text Files (*.txt);;All Files (*)", options=options)
        if file_name:
            self.clear_entries()
            recipe_name = os.path.splitext(os.path.basename(file_name))[0].replace('_', ' ')
            self.recipe_name_entry.setText(recipe_name)
            with open(file_name, 'r') as file:
                lines = file.readlines()
                mode = None
                for line in lines:
                    line = line.strip()
                    print(f"Reading line: {line}")  # Debugging statement
                    if line == "Ingredients:":
                        mode = "ingredients"
                    elif line == "Preparation:":
                        mode = "preparation"
                    elif line == "URL:":
                        mode = "url"
                    elif line == "Image URL:":
                        mode = "image_url"
                    elif mode == "ingredients" and line:
                        self.ingredients_list.addItem(line)
                    elif mode == "preparation" and line:
                        self.preparation_text.append(line)
                    elif mode == "url" and line:
                        self.url_entry.setText(line)
                    elif mode == "image_url" and line:
                        self.image_url_entry.setText(line)
                        self.load_image()

    def clear_entries(self):
        self.recipe_name_entry.clear()
        self.product_combobox.combo_box.setCurrentIndex(0)
        self.unit_combobox.setCurrentIndex(0)
        self.amount_entry.clear()
        self.ingredients_list.clear()
        self.preparation_text.clear()
        self.url_entry.clear()
        self.image_url_entry.clear()
        self.image_label.clear()
        self.product_combobox.search_bar.clear()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = RecipeApp()
    ex.showFullScreen()
    sys.exit(app.exec_())
