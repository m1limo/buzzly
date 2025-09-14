import sqlite3

# connect to your database
conn = sqlite3.connect("buzzly.db")
cur = conn.cursor()

# 🔑 reset existing admin password
cur.execute("UPDATE admin SET password = ? WHERE username = ?", ("newpassword", "admin"))

# 👤 add another admin user
cur.execute("INSERT INTO admin (username, password) VALUES (?, ?)", ("franklin", "12345"))

conn.commit()
conn.close()

print("✅ Admin password reset and new user added successfully!")
