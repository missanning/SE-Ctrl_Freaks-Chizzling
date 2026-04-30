from tkinter import messagebox

def auto_deduct_stock(cursor, product_id, quantity_sold):
    cursor.execute("SELECT stock FROM products WHERE id = ?", (product_id,))
    result = cursor.fetchone()

    if result:
        current_stock = result[0]
        new_stock = current_stock - quantity_sold

        if new_stock < 0:
            messagebox.showerror("Stock Error", "Not enough stock to complete the sale.")
            return False

        cursor.execute(
            "UPDATE products SET stock = ? WHERE id = ?",
            (new_stock, product_id)
        )
        return True
    else:
        messagebox.showerror("Product Error", "Product not found.")
        return False