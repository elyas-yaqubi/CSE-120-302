import streamlit as st
import base64
import sqlite3
import bcrypt
from sqlalchemy import create_engine, Column, String
from sqlalchemy.orm import sessionmaker, declarative_base

st.set_page_config(initial_sidebar_state="collapsed")

st.markdown(
    """
<style>
    [data-testid="collapsedControl"] {
        display: none
    }
</style>
""",
    unsafe_allow_html=True,
)
# Database setup
DATABASE_URL = "sqlite:///users.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    username = Column(String, primary_key=True)
    password_hash = Column(String)

Base.metadata.create_all(engine)

# Utility functions
def get_user(username):
    session = SessionLocal()
    user = session.query(User).filter_by(username=username).first()
    session.close()
    return user

def create_user(username, password):
    session = SessionLocal()
    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    new_user = User(username=username, password_hash=hashed_password)
    session.add(new_user)
    session.commit()
    session.close()

def authenticate(username, password):
    user = get_user(username)
    if user and bcrypt.checkpw(password.encode(), user.password_hash.encode()):
        return True
    return False

# Streamlit UI
def main():
    
    st.title("Login Page")
    
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        set_background("x10ebackground.jpg")
        login_form()
    else:
        
        
        if st.button("Logout"):
            logout()

def login_form():
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if authenticate(username, password):
            st.session_state.authenticated = True
            st.switch_page("pages/dashboard.py")
        else:
            st.error("Invalid username or password")

    if st.button("Register"):
        if get_user(username):
            st.error("Username already exists!")
        else:
            create_user(username, password)
            st.success("User registered! Please log in.")


def set_background(image_file):
    with open(image_file, "rb") as img_file:
        encoded_string = base64.b64encode(img_file.read()).decode()
 
    bg_image = f"""
    <style>
    .stApp {{
        background-image: url("data:image/jpeg;base64,{encoded_string}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    </style>
    """
    st.markdown(bg_image, unsafe_allow_html=True)

def logout():
    st.session_state.authenticated = False
    st.experimental_rerun()



if __name__ == "__main__":
    main()
