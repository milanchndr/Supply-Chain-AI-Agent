import bcrypt

password_to_hash = b"12345678" # Use the SAME password you set in Supabase Auth
hashed_password_bytes = bcrypt.hashpw(password_to_hash, bcrypt.gensalt())
hashed_password_string = hashed_password_bytes.decode('utf-8')

print(f"User's Supabase Auth Password: {password_to_hash.decode('utf-8')}")
print(f"Bcrypt hash for public.users: {hashed_password_string}")