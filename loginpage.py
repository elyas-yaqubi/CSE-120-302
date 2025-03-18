import streamlit as st
import base64

def main():
    st.title("Login Page")
    
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        set_background("x10ebackground.jpg")
        login_form()
    else:
        st.success("You are logged in!")
        st.button("Logout", on_click=logout)

def login_form():
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if authenticate(username, password):
            st.session_state.authenticated = True
            st.experimental_rerun()
        else:
            st.error("Invalid username or password")

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




def authenticate(username, password):
    valid_users = {"user": "password123"}  # Replace with real authentication logic
    return valid_users.get(username) == password

def logout():
    st.session_state.authenticated = False
    st.experimental_rerun()

if __name__ == "__main__":
    main()