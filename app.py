import re
import html
import streamlit as st
from google import genai
from twilio.rest import Client

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Kaya AI | Health Report Summarizer",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ==========================================
# 2. SESSION STATE
# ==========================================
defaults = {
    "started": False,
    "user_name": "",
    "whatsapp_number": "",
    "help_topic": "Blood Test / Lab Report",
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ==========================================
# 3. CUSTOM DESIGN
# ==========================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

.stApp {
    background: linear-gradient(135deg, #f0f7ff, #f7fbff, #edf8f5);
    font-family: 'Inter', sans-serif;
}
.block-container {
    max-width: 1050px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}
.brand {
    color: #14776f;
    font-size: 1.6rem;
    font-weight: 800;
    margin-bottom: 1.5rem;
    letter-spacing: -0.5px;
}
.hero {
    background: linear-gradient(125deg, #123f58, #16776e);
    padding: 3rem 2.5rem;
    border-radius: 24px;
    margin-bottom: 1.5rem;
    box-shadow: 0 15px 40px rgba(18, 63, 88, 0.15);
}
.hero h1 {
    color: white;
    font-size: clamp(2rem, 5vw, 3.1rem);
    line-height: 1.2;
}
.hero p {
    color: #e2f3f3;
    font-size: 1.05rem;
    line-height: 1.8;
}
.tag {
    display: inline-block;
    color: white;
    background: rgba(255,255,255,0.15);
    border: 1px solid rgba(255,255,255,0.2);
    padding: 8px 14px;
    border-radius: 25px;
    font-size: 0.8rem;
}
.section-title {
    color: #153d51;
    font-size: 1.5rem;
    font-weight: 800;
    margin-top: 1.5rem;
    margin-bottom: 0.8rem;
}
.feature {
    background: white;
    border: 1px solid #e0eaf0;
    border-radius: 16px;
    padding: 1.2rem;
    min-height: 140px;
    margin-bottom: 1rem;
}
.feature h4 { color: #17485b; }
.feature p {
    color: #657b89;
    font-size: 0.9rem;
    line-height: 1.6;
}
div[data-testid="stForm"] {
    background: white;
    padding: 1.5rem;
    border: 1px solid #e0eaf0;
    border-radius: 20px;
    box-shadow: 0 8px 30px rgba(20,60,80,0.05);
}
.stButton > button,
div[data-testid="stFormSubmitButton"] > button {
    background: #147b72;
    color: white;
    border-radius: 12px;
    border: none;
    min-height: 3rem;
    font-weight: 700;
}
.stButton > button:hover,
div[data-testid="stFormSubmitButton"] > button:hover {
    background: #105e58;
    color: white;
    border: none;
}
.notice {
    background: #eaf4f4;
    color: #355968;
    padding: 1rem;
    border-radius: 12px;
    line-height: 1.7;
    font-size: 0.9rem;
    margin-top: 1rem;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. BRAND HEADER
# ==========================================
st.markdown(
    '<div class="brand">🩺 Kaya '
    '<span style="color:#78939c;">AI</span></div>',
    unsafe_allow_html=True,
)

# ==========================================
# 5. WELCOME PAGE
# ==========================================
if not st.session_state.started:
    st.markdown("""
    <div class="hero">
        <div class="tag">✦ YOUR HEALTH, MADE EASIER TO UNDERSTAND</div>
        <h1>Medical reports,<br>in simple language.</h1>
        <p>
            Hello and welcome to Kaya AI! Medical reports can sometimes
            be difficult to understand. Our goal is to help you explore
            lab reports and understand medical terminology in clear,
            simple language.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
        '<div class="section-title">A simpler way to understand your reports</div>',
        unsafe_allow_html=True,
    )
    st.write("Tell us a little about yourself and what you need help with.")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="feature">
            <h4>📄 Report Explorer</h4>
            <p>Upload a medical report or laboratory result.</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="feature">
            <h4>💡 Simple Explanations</h4>
            <p>Explore medical terminology in everyday language.</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="feature">
            <h4>🔒 Privacy Awareness</h4>
            <p>Be mindful of sensitive health details while testing.</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(
        '<div class="section-title">Let’s get to know you 👋</div>',
        unsafe_allow_html=True,
    )

    with st.form("welcome_form"):
        name = st.text_input(
            "What is your name?",
            placeholder="Enter your name",
        )
        whatsapp = st.text_input(
            "Your WhatsApp number",
            placeholder="Example: +919876543210",
            help="Enter your number including country code to receive WhatsApp summaries.",
        )
        topic = st.selectbox(
            "What would you like help understanding?",
            [
                "Blood Test / Lab Report",
                "Medical Report",
                "Understanding Test Values",
                "General Health Information",
                "Something Else",
            ],
        )
        submitted = st.form_submit_button(
            "✨ Let's Explore Everything",
            use_container_width=True,
        )

    if submitted:
        clean_name = name.strip()
        clean_whatsapp = whatsapp.strip()

        if not clean_name:
            st.error("Please enter your name.")
        elif len(clean_name) > 80:
            st.error("Please enter a shorter name.")
        elif clean_whatsapp and not re.fullmatch(
            r"\+?[0-9\s\-()]{7,20}", clean_whatsapp
        ):
            st.error(
                "Please check your WhatsApp number, including country code, "
                "or leave it blank."
            )
        else:
            st.session_state.user_name = clean_name
            st.session_state.whatsapp_number = clean_whatsapp
            st.session_state.help_topic = topic
            st.session_state.started = True
            st.rerun()

    st.markdown("""
    <div class="notice">
        <b>Important:</b> Kaya AI is intended for educational information,
        not diagnosis or treatment. Discuss medical results with a qualified
        healthcare professional. Avoid uploading identifiable medical records
        while testing.
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 6. USER DASHBOARD
# ==========================================
else:
    safe_name = html.escape(st.session_state.user_name)

    st.markdown(f"""
    <div class="hero">
        <div class="tag">✦ YOUR PERSONAL REPORT SPACE</div>
        <h1>Hello, {safe_name}! 👋</h1>
        <p>
            Welcome to Kaya AI. Let's get started with the information
            you want to understand.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
        '<div class="section-title">Your Workspace</div>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        st.write("**Selected topic**")
        st.info(st.session_state.help_topic)
    with col2:
        st.write("**Target WhatsApp**")
        st.info(st.session_state.whatsapp_number or "Not provided")

    st.divider()
    st.subheader("📄 Upload Your Medical Report")
    uploaded_file = st.file_uploader(
        "Choose a PDF or image",
        type=["pdf", "png", "jpg", "jpeg"],
    )

    if uploaded_file is not None:
        st.success("Report uploaded successfully!")
        st.write("**File name:**", uploaded_file.name)
        st.write("**File size:**", f"{uploaded_file.size:,} bytes")

        if uploaded_file.type.startswith("image/"):
            st.image(
                uploaded_file,
                caption="Report Preview",
                use_container_width=True,
            )
        elif uploaded_file.type == "application/pdf":
            st.info("Your PDF is ready for analysis.")

        st.write("")
        if st.button("✨ Summarize & Send to WhatsApp"):
            with st.spinner("Analyzing report with Gemini and sending to WhatsApp..."):
                try:
                    # 1. Generate summary using Gemini SDK
                    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
                    
                    response = client.models.generate_content(
                        model="gemini-1.5-flash",
                        contents="Provide a short, simple, educational summary of this health report file."
                    )
                    
                    summary_text = response.text
                    st.subheader("AI Summary")
                    st.write(summary_text)

                    # 2. Send via Twilio WhatsApp API
                    account_sid = st.secrets["TWILIO_ACCOUNT_SID"]
                    auth_token = st.secrets["TWILIO_AUTH_TOKEN"]
                    client_twilio = Client(account_sid, auth_token)

                    recipient_number = st.session_state.whatsapp_number or "+919876543210"

                    message = client_twilio.messages.create(
                        from_="whatsapp:+17372508034",  # Twilio Sandbox number
                        body=f"Hi {st.session_state.user_name}! Kaya AI Report Summary:\n\n{summary_text}",
                        to=f"whatsapp:{recipient_number}"
                    )
                    
                    st.success(f"Successfully sent to WhatsApp! (SID: {message.sid})")

                except Exception as e:
                    st.error("An error occurred during generation or messaging.")
                    st.code(str(e))

    st.markdown("""
    <div class="notice">
        <b>Privacy reminder:</b> Do not upload identifiable medical records
        while testing.
    </div>
    """, unsafe_allow_html=True)

    if st.button("← Back to Welcome Page"):
        st.session_state.started = False
        st.rerun()