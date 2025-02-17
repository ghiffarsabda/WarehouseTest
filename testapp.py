import streamlit as st
import pandas as pd
import psycopg2

# Database credentials
PGHOST='ep-young-sound-a5fmuzwl.us-east-2.aws.neon.tech'
PGDATABASE='finance_data'
PGUSER='neondb_owner'
PGPASSWORD='uqAcYd9sF3xl'


# --- Database Connection Function ---
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=PGHOST,
            database=PGDATABASE,
            user=PGUSER,
            password=PGPASSWORD,
            sslmode='require'  # Add sslmode for secure connection
        )
        return conn
    except psycopg2.Error as e:
        st.error(f"Error connecting to database: {e}")
        return None

# --- Initialize database table (if it doesn't exist) ---
def initialize_database():
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    sku VARCHAR(255) PRIMARY KEY,
                    product_name VARCHAR(255),
                    stock_level INTEGER DEFAULT 0
                );
            """)
            conn.commit()
            cur.close()
            conn.close()
            st.success("Database and table initialized (if they didn't exist).")
        except psycopg2.Error as e:
            st.error(f"Error initializing database: {e}")


# --- Function to add a new product ---
def add_product(sku, product_name):
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO products (sku, product_name) VALUES (%s, %s) ON CONFLICT (sku) DO NOTHING;",
                (sku, product_name)
            )
            conn.commit()
            cur.close()
            conn.close()
            st.success(f"Product {product_name} (SKU: {sku}) added/updated.")
        except psycopg2.Error as e:
            st.error(f"Error adding product: {e}")

# --- Function to update stock level ---
def update_stock(sku, quantity_change):
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute(
                "UPDATE products SET stock_level = stock_level + %s WHERE sku = %s;",
                (quantity_change, sku)
            )
            conn.commit()
            cur.close()
            conn.close()
            return True  # Indicate success
        except psycopg2.Error as e:
            st.error(f"Error updating stock: {e}")
            return False #Indicate failure


# --- Function to fetch all products ---
def fetch_products():
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT sku, product_name, stock_level FROM products;")
            products = cur.fetchall()
            cur.close()
            conn.close()
            return products
        except psycopg2.Error as e:
            st.error(f"Error fetching products: {e}")
            return []

# --- Callback function for Stock Out ---
def stock_out_callback():
    sku = st.session_state.stock_out
    if sku:
        if update_stock(sku, -1):  # Deduct 1 from stock
            st.success(f"Stock out recorded for SKU: {sku}")
        st.session_state.stock_out = ""  # Clear the text input

# --- Callback function for Stock In ---
def stock_in_callback():
    sku = st.session_state.stock_in
    if sku:
        if update_stock(sku, 1):  # Add 1 to stock
            st.success(f"Stock in recorded for SKU: {sku}")
        st.session_state.stock_in = ""  # Clear the text input


# --- Streamlit App ---
def main():
    st.title("Inventory Management System")

    initialize_database()  # Initialize the database if it doesn't exist.

    # --- Product Database Section ---
    st.header("Product Database")
    with st.form(key="product_form"):
        product_name = st.text_input("Product Name:", key="product_name_input")
        sku = st.text_input("SKU:", key="sku_input")
        submit_product = st.form_submit_button("Add/Update Product")

        if submit_product:
            if product_name and sku:
                add_product(sku, product_name)
                st.session_state.product_name_input = "" # Clear input field
                st.session_state.sku_input = ""  # Clear input field
                st.rerun() # Refresh to update the table
            else:
                st.warning("Product Name and SKU are required.")


    # --- Stock Out Section ---
    st.header("Scan Stock Out")
    st.text_input("Scan SKU to Stock Out (Enter to deduct 1):", key="stock_out", on_change=stock_out_callback)

    # --- Stock In Section ---
    st.header("Scan Stock In")
    st.text_input("Scan SKU to Stock In (Enter to add 1):", key="stock_in", on_change=stock_in_callback)


    # --- Available Products Section ---
    st.header("Available Products")
    products = fetch_products()
    if products:
        df = pd.DataFrame(products, columns=["SKU", "Product Name", "Stock Level"])
        st.dataframe(df)
    else:
        st.info("No products found. Add products to the database.")


if __name__ == "__main__":
    main()
