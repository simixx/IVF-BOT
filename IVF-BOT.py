import streamlit as st
import sqlite3
from sqlite3 import Error
from langchain.prompts import PromptTemplate
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.llms import Ollama
from langchain.chains import RetrievalQA
import pandas as pd

DB_FAISS_PATH = 'vectorstores/db_faiss'

custom_prompt_template = """You are an IVF bot which helps patients in pursuing or starting their IVF journey. You assist with everything including social, financial, legal, procedures, and mental health aspects, and provide guidance about the same.

# Context: {context}

# Question: {question}

Only return the helpful answer below and nothing else.
Answer:
"""

def set_custom_prompt():
    prompt = PromptTemplate(template=custom_prompt_template, input_variables=['context', 'question'])
    return prompt

def retrieval_qa_chain(llm, prompt, db):
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type='stuff',
        retriever=db.as_retriever(search_kwargs={'k': 2}),
        return_source_documents=False,
        chain_type_kwargs={'prompt': prompt}
    )
    return qa_chain

def load_llm():
    llm = Ollama(model="ivfbot")
    return llm

def qa_bot():
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2", model_kwargs={'device': 'cpu'})
    db = FAISS.load_local(DB_FAISS_PATH, embeddings, allow_dangerous_deserialization=True)
    llm = load_llm()
    qa_prompt = set_custom_prompt()
    qa = retrieval_qa_chain(llm, qa_prompt, db)
    return qa

def final_result(query, context=""):
    qa_result = qa_bot()
    response = qa_result({'query': query, 'context': context})
    answer = response.get('result', '')
    return answer

def create_connection():
    conn = None
    try:
        conn = sqlite3.connect('ivf_bot.db')
        return conn
    except Error as e:
        print(e)
    return conn

def create_tables(conn):
    try:
        c = conn.cursor()
        c.execute(""" 
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                role TEXT NOT NULL,
                name TEXT,
                age INTEGER,
                medical_history TEXT,
                progress TEXT,
                BMI TEXT,
                maternal_age TEXT,
                total_failures TEXT,
                ivf_cycles INTEGER,
                duration_of_infertility TEXT,
                amh TEXT,
                type_of_infertility TEXT,
                sperm_type TEXT,
                bhcg TEXT,
                additional_ailments TEXT
            );
        """)
        conn.commit()
    except Error as e:
        print(e)

def insert_user(conn, user):
    sql = ''' 
        INSERT INTO users(username, password, role, name, age, medical_history, progress, BMI, maternal_age, total_failures, ivf_cycles, duration_of_infertility, amh, type_of_infertility, sperm_type, bhcg, additional_ailments)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    '''
    cur = conn.cursor()
    cur.execute(sql, user)
    conn.commit()
    return cur.lastrowid

def authenticate_user(conn, username, password, role):
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username=? AND password=? AND role=?", (username, password, role))
    rows = cur.fetchall()
    return rows

def get_user_by_id(conn, user_id):
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id=?", (user_id,))
    rows = cur.fetchall()
    return rows

def get_all_patients(conn):
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE role='Patient'")
    rows = cur.fetchall()
    return rows

def update_progress(conn, user_id, progress):
    sql = ''' 
        UPDATE users
        SET progress = ?
        WHERE id = ?
    '''
    cur = conn.cursor()
    cur.execute(sql, (progress, user_id))
    conn.commit()

def update_patient_params(conn, user_id, BMI, maternal_age, total_failures, ivf_cycles, duration_of_infertility, amh, type_of_infertility, sperm_type, bhcg, additional_ailments):
    sql = ''' 
        UPDATE users
        SET BMI = ?,
            maternal_age = ?,
            total_failures = ?,
            ivf_cycles = ?,
            duration_of_infertility = ?,
            amh = ?,
            type_of_infertility = ?,
            sperm_type = ?,
            bhcg = ?,
            additional_ailments = ?
        WHERE id = ?
    '''
    cur = conn.cursor()
    cur.execute(sql, (BMI, maternal_age, total_failures, ivf_cycles, duration_of_infertility, amh, type_of_infertility, sperm_type, bhcg, additional_ailments, user_id))
    conn.commit()

def username_exists(conn, username):
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username=?", (username,))
    rows = cur.fetchall()
    return len(rows) > 0

def handle_logout():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.session_state.logged_out = True

def main():
    conn = create_connection()
    create_tables(conn)

    st.markdown(
        """
        <style>
        .stApp {
            background: black;
            cbackground-color: 28282B;
            color: #D63B8E;
        }
        .header {
            color: #E91E63;
            font-size: 2.5em;
            font-weight: bold;
            text-align: center;
            margin-top: 0;
        }
        .welcome-animation {
            font-size: 1em;
            color: white;
            font-style: italic;
            animation: fadeIn 3s ease-in-out;
            text-align: center;
        }
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    if 'logged_out' in st.session_state and st.session_state.logged_out:
        st.success("You have been logged out successfully.")
        del st.session_state.logged_out

    if "user_id" not in st.session_state:
        st.markdown("<h1 class='header'>Welcome to the IVF Journey</h1>", unsafe_allow_html=True)
        st.markdown("<div class='welcome-animation'>We are here to support you every step of the way.</div>", unsafe_allow_html=True)

        st.sidebar.write("New User? Signup here!")
        new_user = st.sidebar.radio("Signup as", ("Patient", "Clinician"), key="signup_role")
        new_username = st.sidebar.text_input("Enter Username", key="signup_username")
        new_password = st.sidebar.text_input("Enter Password", type="password", key="signup_password")
        new_name = st.sidebar.text_input("Enter Full Name", key="signup_name")
        new_age = st.sidebar.number_input("Enter Age", min_value=0, key="signup_age")
        new_medical_history = st.sidebar.text_area("Enter Medical History", key="signup_medical_history")

        if st.sidebar.button("Signup"):
            if username_exists(conn, new_username):
                st.sidebar.error("Username already exists. Please choose a different username.")
            else:
                if new_user == "Patient":
                    role = "Patient"
                    user = (new_username, new_password, role, new_name, new_age, new_medical_history, "", "", "", "", 0, "", "", "", "", "", "")
                    insert_user(conn, user)
                    st.sidebar.success("Patient account created successfully!")
                elif new_user == "Clinician":
                    role = "Clinician"
                    user = (new_username, new_password, role, new_name, None, None, None, "", "", "", 0, "", "", "", "", "", "")
                    insert_user(conn, user)
                    st.sidebar.success("Clinician account created successfully!")

        option = st.selectbox('Login as', ('Patient', 'Clinician'))

        if option == 'Patient':
            st.subheader('Patient Login')
            username = st.text_input('Username')
            password = st.text_input('Password', type='password')
            if st.button('Login'):
                user = authenticate_user(conn, username, password, 'Patient')
                if user:
                    st.session_state['user_id'] = user[0][0]
                    st.session_state['role'] = 'Patient'
                    st.success('Logged in as Patient')
                    st.experimental_rerun()
                else:
                    st.error('Invalid username or password')

        elif option == 'Clinician':
            st.subheader('Clinician Login')
            username = st.text_input('Username')
            password = st.text_input('Password', type='password')
            if st.button('Login'):
                user = authenticate_user(conn, username, password, 'Clinician')
                if user:
                    st.session_state['user_id'] = user[0][0]
                    st.session_state['role'] = 'Clinician'
                    st.success('Logged in as Clinician')
                    st.experimental_rerun()
                else:
                    st.error('Invalid username or password')

    else:
        if st.sidebar.button("Logout"):
            handle_logout()
            st.experimental_rerun()

        if st.session_state['role'] == 'Patient':
            st.subheader('Patient Dashboard')
            user_id = st.session_state['user_id']
            user_data = get_user_by_id(conn, user_id)[0]

            # st.subheader("Update Patient Parameters")
            with st.form(key="update_patient_params_forms"):
                col1, col2 = st.columns(2)

                with col1:
                    ivf_cycles = st.number_input("Number of IVF Cycles", key="ivf_cycles")
                    duration_of_infertility = st.text_input("Duration of Infertility", key="duration_of_infertility")
                    amh = st.text_input("AMH", key="amh")
                    bmi = st.text_input("BMI", key="bmi")
                    maternal_age = st.text_input("Maternal Age", key="maternal_age")
                    total_failures = st.text_input("Total Previous Failures", key="total_failures")

                with col2:
                    type_of_infertility = st.text_input("Type of Infertility", key="type_of_infertility")
                    sperm_type = st.text_input("Sperm Type", key="sperm_type")
                    bhcg = st.selectbox("BhCG (Positive/Negative)", ["Positive", "Negative"], key="bhcg")
                    additional_ailments = st.text_input("Additional Ailments", key="additional_ailments")

                submit_button = st.form_submit_button()
                if submit_button:
                    update_patient_params(
                        conn,
                        st.session_state["user_id"],
                        bmi,
                        maternal_age,
                        total_failures,
                        ivf_cycles,
                        duration_of_infertility,
                        amh,
                        type_of_infertility,
                        sperm_type,
                        bhcg,
                        additional_ailments
                    )
                    st.success('Patient parameters updated successfully.')

            st.header("Your Details")
            if user_data:
                user_details = {
                    "Name": user_data[4],
                    "Age": user_data[5],
                    "Medical History": user_data[6],
                    "BMI": user_data[8],
                    "Maternal Age": user_data[9],
                    "Total Failures": user_data[10],
                    "IVF Cycles": user_data[11],
                    "Duration of Infertility": user_data[12],
                    "AMH": user_data[13],
                    "Type of Infertility": user_data[14],
                    "Sperm Type": user_data[15],
                    "BHCG": user_data[16],
                    "Additional Ailments": user_data[17]
                }
                st.table(user_details.items())

        elif st.session_state['role'] == 'Clinician':
            st.subheader("Welcome, You can find your patients here!")
            patients = get_all_patients(conn)
            df = pd.DataFrame(patients, columns=["ID", "Username", "Password", "Role", "Name", "Age", "Medical History", "Progress", "BMI", "Maternal Age", "Total Failures", "IVF Cycles", "Duration of Infertility", "AMH", "Type of Infertility", "Sperm Type", "BHCG", "Additional Ailments"])
            st.dataframe(df)

            user_id = st.number_input("Enter Patient ID to Update Progress", min_value=1)
            progress = st.text_area("Update Progress")

            if st.button("Update Progress"):
                update_progress(conn, user_id, progress)
                st.success("Progress updated successfully!")

        st.title("IVF Counseling Chat")
    
        if 'messages' not in st.session_state:
            st.session_state.messages = []

        for message in st.session_state.messages:
            st.chat_message(message['role']).markdown(message['content'])

        with st.form(key='message_form', clear_on_submit=True):
            user_input = st.text_area("You: ", "", key='user_input')
            submit_button = st.form_submit_button("Send")
        
        if submit_button and user_input:
            st.session_state.messages.append({'role': 'user', 'content': user_input})
            bot = qa_bot()
            response = bot.run(user_input)
            st.session_state.messages.append({'role': 'assistant', 'content': response})
            st.experimental_rerun()

if __name__ == '__main__':
    main()