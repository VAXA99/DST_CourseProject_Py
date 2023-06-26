import sys
import psycopg2
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QPlainTextEdit, QSizePolicy, QDialog, QTableWidget, QTableWidgetItem, QDialogButtonBox, QComboBox, QGridLayout

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("DST_course_project")
        self.setMinimumSize(800, 600)

        self.connection = None
        self.cursor = None

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.setup_ui()

        database_names = self.load_database_names()
        self.database_input.addItems(database_names)

        self.set_style_sheet()

    def setup_ui(self):
        self.host_label = QLabel("Host:")
        self.host_input = QLineEdit("localhost")
        self.database_label = QLabel("Database:")
        self.database_input = QComboBox()
        self.user_label = QLabel("Username:")
        self.user_input = QLineEdit("postgres")
        self.password_label = QLabel("Password:")
        self.password_input = QLineEdit("123456")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.connect_to_database)

        self.layout.addWidget(self.host_label)
        self.layout.addWidget(self.host_input)
        self.layout.addWidget(self.database_label)
        self.layout.addWidget(self.database_input)
        self.layout.addWidget(self.user_label)
        self.layout.addWidget(self.user_input)
        self.layout.addWidget(self.password_label)
        self.layout.addWidget(self.password_input)
        self.layout.addWidget(self.connect_button)

        self.table_combo = QComboBox()
        self.table_combo.currentIndexChanged.connect(self.load_table_data)
        self.layout.addWidget(self.table_combo)

        self.table = QTableWidget()
        self.layout.addWidget(self.table)

        self.delete_row_button = QPushButton("Delete Row")
        self.delete_row_button.clicked.connect(self.delete_selected_row)
        self.layout.addWidget(self.delete_row_button)

        self.edit_row_button = QPushButton("Edit Row")
        self.edit_row_button.clicked.connect(self.edit_selected_row)
        self.layout.addWidget(self.edit_row_button)

        self.add_row_button = QPushButton("Add Row")
        self.add_row_button.clicked.connect(self.add_row)
        self.layout.addWidget(self.add_row_button)

        self.query_label = QLabel("SQL Query:")
        self.query_input = QPlainTextEdit()
        self.query_input.setDisabled(True)
        self.query_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.layout.addWidget(self.query_label)
        self.layout.addWidget(self.query_input)

        self.query_button = QPushButton("Execute Query")
        self.query_button.clicked.connect(self.execute_query)
        self.query_button.setDisabled(True)
        self.layout.addWidget(self.query_button)

    def set_style_sheet(self):
        style_sheet = """
            QMainWindow {
                background-color: #f2f2f2;
            }

            QLineEdit {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                padding: 4px;
            }

            QPushButton {
                background-color: #ffffff;
                color: #000000;
                padding: 6px 12px;
                border: none;
                border-radius: 3px;
                font-weight: bold;
            }

            QPushButton#deleteButton {
                background-color: #ff0000;
                color: #ffffff;
            }

            QPushButton:hover {
                background-color: #eeeeee;
            }

            QPushButton:pressed {
                background-color: #dddddd;
            }

            QTableWidget {
                background-color: #ffffff;
                border: 1px solid #cccccc;
            }

            QTableWidget::item:selected {
                background-color: #cceeff;
            }

            QComboBox {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                padding: 4px;
                min-width: 150px;
            }

            QLabel {
                font-weight: bold;
                font-size: 14px;
            }

            QPlainTextEdit {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                padding: 4px;
                font-family: "Courier New";
                font-size: 12px;
            }

            QDialog {
                background-color: #f2f2f2;
            }
        """
        self.setStyleSheet(style_sheet)

    def connect_to_database(self):
        host = self.host_input.text()
        user = self.user_input.text()
        password = self.password_input.text()
        database = self.database_input.currentText()

        try:
            connection = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                database=database

            )
            connection.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = connection.cursor()
            cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false")
            database_names = [result[0] for result in cursor.fetchall()]
            self.database_input.clear() 
            self.database_input.addItems(database_names)
            if self.database_input.count() > 0:
                self.database_input.setCurrentIndex(0)
            self.connection = connection
            self.cursor = cursor
            self.load_table_names()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to connect to the database: {e}")

            
    def load_database_names(self):
        try:
            connection = psycopg2.connect(
                host=self.host_input.text(),
                user=self.user_input.text(),
                password=self.password_input.text()
            )
            connection.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = connection.cursor()
            cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false")
            return [result[0] for result in cursor.fetchall()]
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to get database names: {e}")
            return []

    def load_table_names(self):
        try:
            self.table_combo.clear()

            self.cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            table_names = [result[0] for result in self.cursor.fetchall()]
            self.table_combo.addItems(table_names)

            # Set the current index to the first table, if available
            if len(table_names) > 0:
                self.table_combo.setCurrentIndex(0)
                self.load_table_data()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load table names: {e}")

    def load_table_data(self):
        table_name = self.table_combo.currentText()
        if table_name:
            try:
                self.cursor.execute(f"SELECT * FROM {table_name}")
                data = self.cursor.fetchall()
                column_names = [desc[0] for desc in self.cursor.description]

                self.table.clear()
                self.table.setColumnCount(len(column_names))
                self.table.setRowCount(len(data))
                self.table.setHorizontalHeaderLabels(column_names)

                for i, row in enumerate(data):
                    for j, value in enumerate(row):
                        item = QTableWidgetItem(str(value))
                        self.table.setItem(i, j, item)

                self.table.resizeColumnsToContents()
                self.table.resizeRowsToContents()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to load table data: {e}")



    def get_primary_key_column(self, table_name):
        try:
            self.cursor.execute(f"SELECT pg_attribute.attname AS column_name "
                                f"FROM pg_index, pg_class, pg_attribute "
                                f"WHERE pg_class.oid = '{table_name}'::regclass "
                                f"AND indrelid = pg_class.oid "
                                f"AND pg_attribute.attrelid = pg_class.oid "
                                f"AND pg_attribute.attnum = any(pg_index.indkey) "
                                f"AND indisprimary")
            primary_key_column = self.cursor.fetchone()
            if primary_key_column:
                return primary_key_column[0]
        except Exception as e:
            print("Error retrieving primary key column:", e)
        return None
    
    def edit_selected_row(self):
        selected_row = self.table.currentRow()
        if selected_row >= 0:
            table_name = self.table_combo.currentText()
            primary_key_column = self.get_primary_key_column(table_name)

            if primary_key_column:
                primary_key = self.table.item(selected_row, 0).text()  # Assuming the first column contains the primary key

                row_values = []
                column_names = []  # Define column_names list

                for col in range(self.table.columnCount()):
                    header_item = self.table.horizontalHeaderItem(col)
                    if header_item is not None:
                        column_name = header_item.text()
                        value = self.table.item(selected_row, col).text()

                        # Convert empty strings to None
                        if value == '':
                            value = None

                        row_values.append(value)
                        column_names.append(column_name)  # Add column_name to the list

                edit_form = EditForm(column_names, row_values)  # Pass column_names and row_values
                if edit_form.exec_() == QDialog.Accepted:
                    edited_values = edit_form.get_updated_values()

                    # Replace None values with NULL placeholders
                    edited_values = [value if value is not None else "NULL" for value in edited_values]

                    update_query = f"UPDATE {table_name} SET "
                    for col, value in enumerate(edited_values):
                        column_name = self.table.horizontalHeaderItem(col).text()
                        value_expr = "NULL" if value == "NULL" else f"'{value}'"  # Handle NULL placeholders
                        update_query += f"{column_name} = {value_expr}, "
                    update_query = update_query[:-2]  # Remove the trailing comma and space
                    update_query += f" WHERE {primary_key_column} = '{primary_key}'"

                    try:
                        self.cursor.execute(update_query)
                        self.connection.commit()
                        self.load_table_data()
                        QMessageBox.information(self, "Success", "Row edited successfully")
                    except Exception as e:
                        QMessageBox.warning(self, "Error", f"Failed to edit row: {e}")
            else:
                QMessageBox.warning(self, "Error", "Primary key not found")
        else:
            QMessageBox.warning(self, "Error", "Select a row to edit")


    def delete_selected_row(self):
        selected_row = self.table.currentRow()
        if selected_row >= 0:
            table_name = self.table_combo.currentText()
            primary_key_column = self.get_primary_key_column(table_name)

            if primary_key_column:
                primary_key = self.table.item(selected_row, 0).text()  # Assuming the first column contains the primary key

                delete_query = f"DELETE FROM {table_name} WHERE {primary_key_column} = '{primary_key}'"
                try:
                    self.cursor.execute(delete_query)
                    self.connection.commit()
                    self.load_table_data()
                    QMessageBox.information(self, "Success", "Row deleted successfully")
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Failed to delete row: {e}")
            else:
                QMessageBox.warning(self, "Error", "Primary key column not found")
        else:
            QMessageBox.warning(self, "Error", "Select a row to delete")

    def add_row(self):
        table_name = self.table_combo.currentText()
        column_names = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())]

        add_form = AddForm(column_names)
        if add_form.exec_():
            row_values = add_form.get_row_values()

            # Replace empty strings with NULL placeholders
            row_values = [value if value is not None else "NULL" for value in row_values]

            insert_query = f"INSERT INTO {table_name} ("
            insert_query += ", ".join(column_names)
            insert_query += ") VALUES ("
            insert_query += ", ".join([f"'{value}'" if value != "NULL" else "NULL" for value in row_values])  # Handle NULL placeholders
            insert_query += ")"

            try:
                self.cursor.execute(insert_query)
                self.connection.commit()
                self.load_table_data()
                QMessageBox.information(self, "Success", "Row added successfully")
            except Exception as e:
                self.connection.rollback()
                QMessageBox.warning(self, "Error", f"Failed to add row: {e}")

    def execute_query(self):
        query = self.query_input.toPlainText()
        try:
            self.cursor.execute(query)
            if query.lower().startswith("select"):
                data = self.cursor.fetchall()
                column_names = [desc[0] for desc in self.cursor.description]

                self.table.clear()
                self.table.setColumnCount(len(column_names))
                self.table.setRowCount(len(data))
                self.table.setHorizontalHeaderLabels(column_names)

                for i, row in enumerate(data):
                    for j, value in enumerate(row):
                        item = QTableWidgetItem(str(value))
                        self.table.setItem(i, j, item)

                self.table.resizeColumnsToContents()
                self.table.resizeRowsToContents()
                QMessageBox.information(self, "Success", "Query executed successfully")
            else:
                self.connection.commit()
                QMessageBox.information(self, "Success", "Query executed successfully")
        except Exception as e:
            self.connection.rollback()
            QMessageBox.warning(self, "Error", f"Failed to execute query: {e}")

class EditForm(QDialog):
    def __init__(self, column_names, values):
        super().__init__()
        self.setWindowTitle("Edit Row")

        self.layout = QGridLayout(self)
        self.row_values = []

        for i, column_name in enumerate(column_names):
            label = QLabel(column_name)
            value = QLineEdit(values[i])
            self.row_values.append(value)
            self.layout.addWidget(label, i, 0)
            self.layout.addWidget(value, i, 1)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        self.layout.addWidget(button_box, len(column_names), 0, 1, 2)

    def get_updated_values(self):
        return [value.text() for value in self.row_values]



class AddForm(QDialog):
    def __init__(self, column_names):
        super().__init__()
        self.setWindowTitle("Add Row")

        self.layout = QVBoxLayout(self)

        self.fields = []

        for column_name in column_names:
            field_label = QLabel(column_name, self)
            field = QLineEdit("")  # Use empty string as a placeholder for NULL values
            self.fields.append(field)
            self.layout.addWidget(field_label)
            self.layout.addWidget(field)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        self.layout.addWidget(button_box)

    def get_row_values(self):
        row_values = [field.text() if field.text() != "" else None for field in self.fields]  # Replace empty strings with None
        return row_values


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
