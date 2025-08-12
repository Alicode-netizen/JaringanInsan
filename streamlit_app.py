import streamlit as st
from datetime import datetime, date
import uuid
import os
import json
import pandas as pd
import graphviz
from supabase import create_client, Client
import base64
import random

# ---------- Configurations ----------
st.set_page_config(page_title="Jalinan Insan", page_icon="👥", layout="wide")
USER_FILE = "users.json"
DATA_DIR = "user_data"
LOGO_PATH = "logoJK.png"

# --- Supabase Setup ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# ---------- Load logo image ----------
def get_image_base64(path):
    try:
        with open(path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception:
        return ""

def render_logo(center=True, size="large"):
    image_base64 = get_image_base64(LOGO_PATH)
    width = 200 if size == "large" else 100
    alignment = "center" if center else "left"
    if image_base64:
        st.markdown(f"<div style='text-align:{alignment};'><img src='data:image/png;base64,{image_base64}' width='{width}'></div>", unsafe_allow_html=True)

# ---------- Helper Functions ----------
def hash_password(password):
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f)

def get_user_data_path(email):
    return os.path.join(DATA_DIR, f"{email}.json")

def load_user_data(email):
    path = get_user_data_path(email)
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {"bio": {}, "history": [], "lifemap": []}

def save_user_data(email, data):
    with open(get_user_data_path(email), "w") as f:
        json.dump(data, f, indent=2)

# ---------- Session State ----------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "user_data" not in st.session_state:
    st.session_state.user_data = {}
if "selected_tool" not in st.session_state:
    st.session_state.selected_tool = None
if "generated_center" not in st.session_state:
    st.session_state.generated_center = None
if "ecomap_graph" not in st.session_state:
    st.session_state.ecomap_graph = graphviz.Digraph()
if "social_graph" not in st.session_state:
    st.session_state.social_graph = graphviz.Digraph()
if "current_genogram" not in st.session_state:
    st.session_state.current_genogram = None

# ---------- Sidebar Login/Signup ----------
with st.sidebar:
    render_logo(size="small")
    st.title("🔐 Login / Sign Up")
    mode = st.radio("Choose Option:", ["Login", "Sign Up"])

    users_db = load_users()
    if mode == "Sign Up":
        new_email = st.text_input("Email", key="signup_email")
        new_pass = st.text_input("Password", type="password", key="signup_pass")
        if st.button("Sign Up"):
            if new_email in users_db:
                st.warning("User already exists.")
            else:
                users_db[new_email] = hash_password(new_pass)
                save_users(users_db)
                st.success("Account created. Please log in.")
    else:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Log In"):
            if email in users_db and users_db[email] == hash_password(password):
                st.session_state.authenticated = True
                st.session_state.user_email = email
                st.session_state.user_data = load_user_data(email)
                # Simulate Supabase session: must be set for messaging
                # Here, we fake a session user dict, but in reality, you'd set this after supabase login
                if "user" not in st.session_state:
                    # Use email as id fallback if not using Supabase auth
                    st.session_state.user = {"id": email, "email": email}
                st.success(f"Welcome, {email}")
            else:
                st.error("Invalid credentials.")

# ---------- Main App ----------
if st.session_state.authenticated and "user" in st.session_state:
    tabs = st.tabs(["🏠 Home", "💬 Messaging", "📚 History", "👤 Biodata", "🧰 Tools"])

    # ---------- Home Tab ----------
    with tabs[0]:
        render_logo()
        st.success("🌟 Welcome to Jalinan Insan")
        bio = st.session_state.user_data.get("bio", {})
        st.markdown(f"**Name:** {bio.get('name', 'Not set')}")
        st.markdown(f"**Email:** {st.session_state.user_email}")
        st.markdown(f"**Place of Birth:** {bio.get('birth_place', 'Not set')}")
        st.success("🌟 Quote of the Day")
        st.info(random.choice([
            "Helping one person might not change the world, but it could change the world for one person.",
            "Orang yang gagal akan nampak alasan pada setiap peluang, manakala orang yang berjaya akan nampak peluang dalam setiap alasan.",
            "Act as if what you do makes a difference. It does.",
            "You play stupid game, you win stupid prizes.",
            "The best revenge is to forgive.",
            "Envy eats away faith just as fire consumes wood.",
            "Pride prevents a man from seeking knowledge.",
            "The worst friend is he who is only with you when you are wealthy and leaves you when you are poor.",
            "kalau tidak dipecahkan ruyung, manakan dapat sagunya.",
            "Susah dahulu, Senang kemudian.",
            "Berani kerana benar, takut kerana salah.",
            "Any problems can occur at any moments, thus confirmation is important.",
            "The past is in the past."
        ]))
        st.markdown("### 📰 Latest News")

    # ---------- Messaging Tab ----------
    with tabs[1]:
        st.header("💬 Messaging")
        current_user_id = st.session_state["user"]["id"]

        # --- Search for contact ---
        st.subheader("Search Contact")
        search_id = st.text_input("Enter user ID to search")
        if search_id:
            result = supabase.table("contacts").select("*").or_(
                f"(requester_id.eq.{current_user_id},requestee_id.eq.{search_id})"
            ).execute()
            if not result.data:
                st.info("No contact found. You may need to send/accept a request first.")
            else:
                st.success("A contact exists with this user.")

        # --- Get user's accepted contacts ---
        contacts_data = supabase.table("contacts").select("*").or_(
            f"(requester_id.eq.{current_user_id},requestee_id.eq.{current_user_id})"
        ).eq("status", "accepted").execute().data

        contact_ids = [
            c["requester_id"] if c["requester_id"] != current_user_id else c["requestee_id"]
            for c in contacts_data
        ]

        st.subheader("Your Contacts")
        if not contact_ids:
            st.info("No accepted contacts yet.")
        else:
            # Get contact labels (email if available, else id)
            contact_options = []
            user_table = supabase.table("users")
            for uid in contact_ids:
                res = user_table.select("email").eq("id", uid).execute()
                if res.data:
                    contact_options.append({"id": uid, "label": res.data[0]["email"]})
                else:
                    contact_options.append({"id": uid, "label": str(uid)})

            contact_labels = [c["label"] for c in contact_options]
            if contact_labels:
                selected_idx = st.selectbox("Choose a contact", range(len(contact_labels)), format_func=lambda i: contact_labels[i])
                selected_contact = contact_options[selected_idx]["id"]

                # --- Load messages ---
                def load_messages():
                    msgs = supabase.table("messages").select("*").or_(
                        f"(sender_id.eq.{current_user_id},receiver_id.eq.{selected_contact}),"
                        f"(sender_id.eq.{selected_contact},receiver_id.eq.{current_user_id})"
                    ).order("created_at", desc=False).execute().data
                    return msgs

                msgs = load_messages()
                st.markdown("### Chat")
                for m in msgs:
                    sender = "You" if m["sender_id"] == current_user_id else next((c["label"] for c in contact_options if c["id"] == m["sender_id"]), str(m["sender_id"]))
                    if m["text"]:
                        st.markdown(f"**{sender}:** {m['text']}  \n<sub>{m['created_at']}</sub>", unsafe_allow_html=True)
                    if m.get("media_url"):
                        if m.get("media_type") == "image/png":
                            st.image(m["media_url"], width=200)
                        elif m.get("media_type") == "application/pdf":
                            st.markdown(f"[📄 PDF File]({m['media_url']})")
                # --- Send new message ---
                st.subheader("Send a Message")
                new_text = st.text_input("Type your message", key="msg_text")
                uploaded_file = st.file_uploader("Send a file (PNG or PDF)", type=["png", "pdf"], key="msg_file")
                if st.button("Send", key="send_btn"):
                    media_url = None
                    media_type = None
                    if uploaded_file is not None:
                        filename = f"{uuid.uuid4()}_{uploaded_file.name}"
                        res = supabase.storage.from_("chat_files").upload(filename, uploaded_file)
                        if res.status_code == 200:
                            media_url = f"{SUPABASE_URL}/storage/v1/object/public/chat_files/{filename}"
                            media_type = uploaded_file.type
                        else:
                            st.error("Failed to upload file.")
                    supabase.table("messages").insert({
                        "sender_id": current_user_id,
                        "receiver_id": selected_contact,
                        "text": new_text if new_text else None,
                        "media_url": media_url,
                        "media_type": media_type
                    }).execute()
                    st.experimental_rerun()
                st.caption("Refresh the page to see new messages. (Polling every page load)")

    # ---------- History Tab ----------
    with tabs[2]:
        st.header("📚 History")
        history_data = st.session_state.user_data.get("history", [])
        if not history_data:
            st.info("No saved maps yet. Create some using the Tools tab!")
        else:
            for i, item in enumerate(history_data):
                st.divider()
                st.subheader(f"{item['type']}: {item['title']}")
                st.caption(f"Created: {item.get('timestamp', 'Unknown')}")
                if item["type"] in ["Genogram", "Ecomap", "Social Network"]:
                    try:
                        st.graphviz_chart(item["dot"])
                    except Exception as e:
                        st.error(f"Could not render diagram: {str(e)}")
                elif item["type"] == "Life Roadmap":
                    if "data" in item:
                        df = pd.DataFrame(item["data"], columns=["Time", "Event", "Impact"])
                        st.line_chart(df.set_index("Time")["Impact"])
                        st.dataframe(df)
                    else:
                        st.warning("No data available for this roadmap")
                if st.button(f"❌ Delete this {item['type']}", key=f"delete_{i}"):
                    del st.session_state.user_data["history"][i]
                    save_user_data(st.session_state.user_email, st.session_state.user_data)
                    st.experimental_rerun()

    # ---------- Biodata Tab ----------
    with tabs[3]:
        st.header("👤 Biodata")
        bio = st.session_state.user_data.get("bio", {})
        with st.form("bio_form"):
            name = st.text_input("Full Name", value=bio.get("name", ""))
            dob = st.date_input("Date of Birth", value=date(2000, 1, 1))
            email = st.text_input("Email", value=st.session_state.user_email)
            marital = st.selectbox("Marital Status", ["Single", "Married", "Divorced", "Widowed"])
            birth = st.text_input("Place of Birth", value=bio.get("birth_place", ""))
            about = st.text_area("About You", value=bio.get("about", ""))
            work = st.text_input("Work/School", value=bio.get("work", ""))
            if st.form_submit_button("Save"):
                st.session_state.user_data["bio"] = {
                    "name": name, "dob": str(dob), "email": email,
                    "marital_status": marital, "birth_place": birth,
                    "about": about, "work": work
                }
                save_user_data(st.session_state.user_email, st.session_state.user_data)
                st.success("Saved.")

    # ---------- Tools Tab ----------
    with tabs[4]:
        st.header("🧰 Tools")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("👨‍👩‍👧‍👦 Genogram"):
                st.session_state.selected_tool = "Genogram"
        with col2:
            if st.button("🌐 Ecomap"):
                st.session_state.selected_tool = "Ecomap"
        with col3:
            if st.button("🤝 Social Network"):
                st.session_state.selected_tool = "Social"
        with col4:
            if st.button("🛣️ Life Roadmap"):
                st.session_state.selected_tool = "Life"
        tool = st.session_state.selected_tool

        # ---------- Genogram ----------
        if tool == "Genogram":
            st.success("🌟 Welcome to Genogram")
            st.header("👨‍👩‍👧‍👦 Genogram")
            with st.form("genogram_form"):
                st.subheader("Father Side")
                father = st.text_input("Father")
                paternal_grandfather = st.text_input("Paternal Grandfather")
                paternal_grandmother = st.text_input("Paternal Grandmother")
                paternal_aunts = st.text_area("Paternal Aunts (comma-separated)")
                paternal_uncles = st.text_area("Paternal Uncles (comma-separated)")

                st.subheader("Mother Side")
                mother = st.text_input("Mother")
                maternal_grandfather = st.text_input("Maternal Grandfather")
                maternal_grandmother = st.text_input("Maternal Grandmother")
                maternal_aunts = st.text_area("Maternal Aunts (comma-separated)")
                maternal_uncles = st.text_area("Maternal Uncles (comma-separated)")

                st.subheader("You")
                user_name = st.text_input("Your Name")
                user_spouse = st.text_input("Spouse")
                user_siblings = st.text_area("Siblings (comma-separated)")
                user_children = st.text_area("Children (comma-separated)")
                submitted = st.form_submit_button("Generate Genogram")

            if submitted:
                dot = graphviz.Digraph()
                def node(name, gender):
                    if gender == "M":
                        dot.node(name, name, shape="box", style="filled", fillcolor="lightblue")
                    else:
                        dot.node(name, name, shape="ellipse", style="filled", fillcolor="pink")
                node(paternal_grandfather, "M")
                node(paternal_grandmother, "F")
                dot.edge(paternal_grandfather, father)
                dot.edge(paternal_grandmother, father)
                node(maternal_grandfather, "M")
                node(maternal_grandmother, "F")
                dot.edge(maternal_grandfather, mother)
                dot.edge(maternal_grandmother, mother)
                node(father, "M")
                node(mother, "F")
                dot.edge(father, user_name)
                dot.edge(mother, user_name)
                for s in [s.strip() for s in user_siblings.split(",") if s.strip()]:
                    node(s, "M")
                    dot.edge(father, s)
                    dot.edge(mother, s)
                if user_spouse.strip():
                    node(user_spouse, "F")
                    dot.edge(user_name, user_spouse, label="marriage")
                for c in [c.strip() for c in user_children.split(",") if c.strip()]:
                    node(c, "F" if random.random() > 0.5 else "M")
                    if user_spouse.strip():
                        dot.edge(user_name, c)
                        dot.edge(user_spouse, c)
                    else:
                        dot.edge(user_name, c)
                st.graphviz_chart(dot)
                st.session_state.current_genogram = {
                    "dot": dot.source,
                    "title": f"Genogram: {user_name}'s Family"
                }

            if 'current_genogram' in st.session_state:
                if st.button("💾 Save to History", key="save_genogram"):
                    history_entry = {
                        "type": "Genogram",
                        "title": st.session_state.current_genogram["title"],
                        "dot": st.session_state.current_genogram["dot"],
                        "timestamp": str(datetime.now())
                    }
                    if "history" not in st.session_state.user_data:
                        st.session_state.user_data["history"] = []
                    st.session_state.user_data["history"].append(history_entry)
                    save_user_data(st.session_state.user_email, st.session_state.user_data)
                    st.success(f"Saved {history_entry['title']} to history!")
                    del st.session_state.current_genogram

        # ---------- Ecomap ----------
        elif tool == "Ecomap":
            st.success("🌟 Welcome to Ecomap")
            st.subheader("🌐 Ecomap Tool")
            center = st.session_state.generated_center or st.text_input("Family Member (center)", value="You")
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Relation factor")
                entity_type = st.selectbox("Relation Type", ["Person", "Work/School", "Pet", "Agency"])
                relation = st.radio("Relation Outcome", ["Positive", "Negative", "Complicated"], horizontal=True)
                direction = st.radio("Relation Direction", ["From user →", "To user ←"], horizontal=True)
                if st.button("➕ Add Connection"):
                    shape = "circle" if entity_type == "Person" else "box"
                    color = {"Positive": "green", "Negative": "red", "Complicated": "orange"}[relation]
                    style = {"Positive": "solid", "Negative": "dashed", "Complicated": "bold"}[relation]
                    label = {"Positive": "─────", "Negative": "⸺⸺⸺", "Complicated": "/\/\/\/"}[relation]
                    st.session_state.ecomap_graph.node(center, center, shape="circle", color="blue")
                    st.session_state.ecomap_graph.node(name, name, shape=shape, color=color)
                    if direction == "From user →":
                        st.session_state.ecomap_graph.edge(center, name, color=color, label=label, style=style)
                    else:
                        st.session_state.ecomap_graph.edge(name, center, color=color, label=label, style=style)
            with col2:
                st.graphviz_chart(st.session_state.ecomap_graph)
                if st.button("💾 Save to History", key="save_ecomap"):
                    title = f"Ecomap: {center}'s Connections"
                    history_entry = {
                        "type": "Ecomap",
                        "title": title,
                        "dot": st.session_state.ecomap_graph.source,
                        "timestamp": str(datetime.now())
                    }
                    if "history" not in st.session_state.user_data:
                        st.session_state.user_data["history"] = []
                    st.session_state.user_data["history"].append(history_entry)
                    save_user_data(st.session_state.user_email, st.session_state.user_data)
                    st.success(f"Saved {title} to history!")
                if st.button("🔄 Reset Ecomap", key="reset_ecomap"):
                    st.session_state.ecomap_graph = graphviz.Digraph()

        # ---------- Social Network ----------
        elif tool == "Social":
            st.success("🌟 Welcome to Social Network Diagram")
            st.header("🫂 Social Network")
            center = st.text_input("Your Name (center)", value="You")
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Connection Name")
                entity_type = st.selectbox("Entity Type", ["Person", "Work/School", "Pet", "Agency"])
                relation = st.radio("Relationship Type", ["Positive", "Negative", "Complicated"], horizontal=True)
                direction = st.radio("Support Direction", ["From user →", "To user ←"], horizontal=True)
                if st.button("➕ Add Connection"):
                    shape = "circle" if entity_type == "Person" else "box"
                    color_map = {"Positive": "green", "Negative": "red", "Complicated": "orange"}
                    style_map = {"Positive": "solid", "Negative": "dashed", "Complicated": "bold"}
                    label_map = {"Positive": "─────", "Negative": "⸺⸺⸺", "Complicated": "/\/\/\/"}
                    st.session_state.social_graph.node(center, center, shape="circle", color="blue")
                    st.session_state.social_graph.node(name, name, shape=shape, color=color_map[relation])
                    if direction == "From user →":
                        st.session_state.social_graph.edge(center, name, 
                                                          color=color_map[relation], 
                                                          label=label_map[relation], 
                                                          style=style_map[relation])
                    else:
                        st.session_state.social_graph.edge(name, center, 
                                                          color=color_map[relation], 
                                                          label=label_map[relation], 
                                                          style=style_map[relation])
            with col2:
                st.graphviz_chart(st.session_state.social_graph)
                if st.button("💾 Save to History", key="save_social"):
                    title = f"Social Network: {center}"
                    history_entry = {
                        "type": "Social Network",
                        "title": title,
                        "dot": st.session_state.social_graph.source,
                        "timestamp": str(datetime.now())
                    }
                    if "history" not in st.session_state.user_data:
                        st.session_state.user_data["history"] = []
                    st.session_state.user_data["history"].append(history_entry)
                    save_user_data(st.session_state.user_email, st.session_state.user_data)
                    st.success(f"Saved {title} to history!")
                if st.button("🔄 Reset Social Network", key="reset_social"):
                    st.session_state.social_graph = graphviz.Digraph()

        # ---------- Life Roadmap ----------
        elif tool == "Life":
            st.success("🌟 Welcome to Life Roadmap")
            st.subheader("🛣️ Life Roadmap")
            with st.form("life_form", clear_on_submit=True):
                time = st.text_input("Time (Year/Age)", placeholder="e.g., 2023 or Age 25")
                event = st.text_input("Event", placeholder="e.g., Graduated from University")
                impact = st.slider("Impact", -10, 10, 0)
                submitted_life = st.form_submit_button("➕ Add Event")
                if submitted_life and time and event:
                    if "lifemap" not in st.session_state.user_data:
                        st.session_state.user_data["lifemap"] = []
                    st.session_state.user_data["lifemap"].append((time, event, impact))
                    save_user_data(st.session_state.user_email, st.session_state.user_data)
            if st.session_state.user_data.get("lifemap"):
                st.subheader("Your Life Roadmap")
                df = pd.DataFrame(st.session_state.user_data["lifemap"], columns=["Time", "Event", "Impact"])
                st.line_chart(df.set_index("Time")["Impact"])
                st.dataframe(df)
                if st.button("💾 Save to History", key="save_life"):
                    title = f"Life Roadmap: {st.session_state.user_data['bio'].get('name', 'My Life')}"
                    history_entry = {
                        "type": "Life Roadmap",
                        "title": title,
                        "data": st.session_state.user_data["lifemap"],
                        "timestamp": str(datetime.now())
                    }
                    if "history" not in st.session_state.user_data:
                        st.session_state.user_data["history"] = []
                    st.session_state.user_data["history"].append(history_entry)
                    save_user_data(st.session_state.user_email, st.session_state.user_data)
                    st.success(f"Saved {title} to history!")

else:
    render_logo()
    st.title("👥 Jalinan Insan")
    st.info("Please log in or sign up to access the app features. Use the sidebar to log in or create a new account.")
