import sys
import psycopg2
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QPlainTextEdit, QSizePolicy, QDialog, QTableWidget, QTableWidgetItem, QDialogButtonBox, QComboBox


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

    def setup_ui(self):
        self.host_label = QLabel("Host:")
        self.host_input = QLineEdit("localhost")
        self.database_label = QLabel("Database:")
        self.database_input = QLineEdit("library")
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

    def connect_to_database(self):
        host = self.host_input.text()
        database = self.database_input.text()
        user = self.user_input.text()
        password = self.password_input.text()

        try:
            self.connection = psycopg2.connect(
                host=host,
                database=database,
                user=user,
                password=password
            )
            self.cursor = self.connection.cursor()
            self.load_table_names()
            self.query_input.setEnabled(True)
            self.query_button.setEnabled(True)
            QMessageBox.information(self, "Success", "Successfully connected to the database")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to connect to the database: {e}")

    def load_table_names(self):
        try:
            self.cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            table_names = [result[0] for result in self.cursor.fetchall()]
            self.table_combo.clear()
            self.table_combo.addItems(table_names)
        except Exception as e:
            print("Error loading table names:", e)

    def load_table_data(self):
        table_name = self.table_combo.currentText()

        try:
            self.cursor.execute(f"SELECT * FROM {table_name}")
            rows = self.cursor.fetchall()
            column_names = [desc[0] for desc in self.cursor.description]

            self.table.clear()
            self.table.setColumnCount(len(column_names))
            self.table.setRowCount(len(rows))
            self.table.setHorizontalHeaderLabels(column_names)

            for row, values in enumerate(rows):
                for col, value in enumerate(values):
                    item = QTableWidgetItem(str(value))
                    self.table.setItem(row, col, item)

        except Exception as e:
            print(f"Error loading data from table {table_name}:", e)

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

    def edit_selected_row(self):
        selected_row = self.table.currentRow()
        if selected_row >= 0:
            table_name = self.table_combo.currentText()
            primary_key_column = self.get_primary_key_column(table_name)

        if primary_key_column:
            primary_key = self.table.item(selected_row, 0).text()  # Assuming the first column contains the primary key

            row_values = []
            for col in range(self.table.columnCount()):
                header_item = self.table.horizontalHeaderItem(col)
                if header_item is not None:
                    column_name = header_item.text()
                    value = self.table.item(selected_row, col).text()
                    row_values.append(value)

            edit_form = EditForm(row_values)
            if edit_form.exec_() == QDialog.Accepted:
                edited_values = edit_form.get_edited_values()

                update_query = f"UPDATE {table_name} SET "
                for col, value in enumerate(edited_values):
                    column_name = self.table.horizontalHeaderItem(col).text()
                    update_query += f"{column_name} = '{value}', "
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
                QMessageBox.warning(self, "Error", "Primary key column not found")
        else:
            QMessageBox.warning(self, "Error", "Select a row to edit")

    def get_primary_key_column(self, table_name):
        try:
            self.cursor.execute(f"SELECT kcu.column_name FROM information_schema.table_constraints AS tc "
                                f"JOIN information_schema.key_column_usage AS kcu ON tc.constraint_name = kcu.constraint_name "
                                f"WHERE tc.table_name = '{table_name}' AND tc.constraint_type = 'PRIMARY KEY'")
            primary_key_column = self.cursor.fetchone()
            if primary_key_column:
                return primary_key_column[0]
        except Exception as e:
            print("Error retrieving primary key column:", e)
        return None

    def execute_query(self):
        query = self.query_input.toPlainText()
        try:
            self.cursor.execute(query)
            if query.strip().split()[0].upper() == 'SELECT':
                rows = self.cursor.fetchall()
                column_names = [desc[0] for desc in self.cursor.description]

                self.table.clear()
                self.table.setColumnCount(len(column_names))
                self.table.setRowCount(len(rows))
                self.table.setHorizontalHeaderLabels(column_names)

                for row, values in enumerate(rows):
                    for col, value in enumerate(values):
                        item = QTableWidgetItem(str(value))
                        self.table.setItem(row, col, item)
            else:
                self.connection.commit()
                self.load_table_data()
                QMessageBox.information(self, "Success", "Query executed successfully")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to execute query: {e}")

class EditForm(QDialog):
    def __init__(self, row_values):
        super().__init__()
        self.setWindowTitle("Edit Row")

        self.layout = QVBoxLayout(self)

        self.fields = []

        for value in row_values:
            field = QLineEdit(self)
            field.setText(value)
            self.fields.append(field)
            self.layout.addWidget(field)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        self.layout.addWidget(button_box)

    def get_edited_values(self):
        return [field.text() for field in self.fields]


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
