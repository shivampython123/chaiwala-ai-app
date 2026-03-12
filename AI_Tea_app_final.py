import streamlit as st
from groq import Groq
import qrcode
from PIL import Image
import io
from twilio.rest import Client
import os
import datetime

# ────────────────────────────────────────────────
#   SECURE CREDENTIAL LOADING
#   Uses Streamlit secrets (cloud/local) with env fallback
#   → NEVER hardcode real keys here!
# ────────────────────────────────────────────────
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY", ""))
TWILIO_ACCOUNT_SID = st.secrets.get("TWILIO_ACCOUNT_SID", os.getenv("TWILIO_ACCOUNT_SID", ""))
TWILIO_AUTH_TOKEN = st.secrets.get("TWILIO_AUTH_TOKEN", os.getenv("TWILIO_AUTH_TOKEN", ""))
TWILIO_FROM_WHATSAPP = "whatsapp:+14155238886"

OWNER_PHONE = st.secrets.get("OWNER_PHONE", os.getenv("OWNER_PHONE", "+917987748574"))

# Quick check – show warning in UI if keys are missing (helps debugging)
if not GROQ_API_KEY:
    st.warning("⚠️ GROQ_API_KEY is missing – check .streamlit/secrets.toml (local) or app secrets (cloud)")
if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
    st.warning("⚠️ Twilio credentials missing – WhatsApp notifications won't work")

# ────────────────────────────────────────────────
#   Clients (only initialize if keys present)
# ────────────────────────────────────────────────
groq_client = None
twilio_client = None

if GROQ_API_KEY:
    try:
        groq_client = Groq(api_key=GROQ_API_KEY)
    except Exception as e:
        st.error(f"Groq client init failed: {e}")

if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    try:
        twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    except Exception as e:
        st.error(f"Twilio client init failed: {e}")

# ────────────────────────────────────────────────
#   Send WhatsApp message
# ────────────────────────────────────────────────
def send_whatsapp(to_phone, message_body):
    if not twilio_client:
        return False, "Twilio client not initialized (missing credentials)"
    if not to_phone.strip():
        return False, "No phone number provided"
    if not to_phone.startswith("+"):
        to_phone = "+91" + to_phone.lstrip("0")
    to_whatsapp = f"whatsapp:{to_phone}"
    try:
        msg = twilio_client.messages.create(
            body=message_body,
            from_=TWILIO_FROM_WHATSAPP,
            to=to_whatsapp
        )
        return True, f"Sent (SID: {msg.sid})"
    except Exception as e:
        return False, str(e)

# ────────────────────────────────────────────────
#   Page setup
# ────────────────────────────────────────────────
st.set_page_config(page_title="ChaiWala AI", page_icon="🫖", layout="wide")

st.title("🫖 ChaiWala AI • Order Your Chai")

with st.expander("WhatsApp Updates – Important"):
    st.markdown("""
    **To get order confirmations & updates on WhatsApp:**
    1. Open WhatsApp
    2. Send `join dozen-huge` to **+14155238886**
    3. Wait for confirmation reply
    4. Enter your number in the form below
    """)

# ────────────────────────────────────────────────
#   ORDER FORM
# ────────────────────────────────────────────────
with st.form("chai_order"):

    col1, col2 = st.columns([5, 4])

    with col1:
        name = st.text_input("Your name", placeholder="Enter your name")
        customer_phone = st.text_input(
            "WhatsApp Number",
            placeholder="Please enter your mobile number like 7987748574 or +917987748574",
            help="Must have joined the Twilio sandbox first"
        )
        cups   = st.number_input("Number of cups", min_value=1, max_value=20, value=1)
        sugar  = st.slider("Sugar (tsp per cup)", 0, 5, 2)
        masala = st.checkbox("Add Masala", value=True)

        tea_type = st.radio("Tea Type", ["Milk Tea", "Masala Tea", "Green Tea", "Black Tea"])
        flavour  = st.multiselect("Extra Flavour", ["Ginger", "Cardamom", "Tulsi", "None"], default=["Ginger"])
        milk     = st.selectbox("Milk Type", ["Full Fat", "Low Fat", "Almond", "None"])

    with col2:
        if st.form_submit_button("Get AI Description", type="secondary"):
            if name.strip() and groq_client:
                with st.spinner("ChaiWala AI is brewing your description..."):
                    try:
                        prompt = f"Greet {name} warmly. Describe this chai order in fun, desi style. Add 1 short useful tip. Order details: {cups} cups of {tea_type}, flavours: {', '.join(flavour)}, masala: {'yes' if masala else 'no'}, sugar {sugar} tsp/cup, milk: {milk}"
                        response = groq_client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[{"role": "user", "content": prompt}],
                            temperature=0.8,
                            max_tokens=180
                        )
                        st.markdown(f"**ChaiWala says:**\n{response.choices[0].message.content.strip()}")
                    except Exception as ex:
                        st.error(f"AI description failed: {ex}")
            elif not groq_client:
                st.error("Groq AI not available – check your API key in secrets")

        # Simple pricing logic
        base_price = 15 if "Milk" in tea_type or "Masala" in tea_type else 12
        addons = len([f for f in flavour if f != "None"]) * 4 + sugar * 2
        total = round((base_price + addons) * cups * 1.18, 1)
        st.markdown(f"**Estimated total: ₹ {total:.1f}** (approx)")

    submitted = st.form_submit_button("PLACE ORDER 🛒", type="primary", use_container_width=True)

if submitted:
    if not name.strip() or not customer_phone.strip():
        st.error("Name and WhatsApp number are required")
    elif not twilio_client:
        st.error("Cannot send WhatsApp – Twilio credentials missing")
    else:
        # Build summary
        summary_lines = [
            f"**New Chai Order**",
            f"Customer: {name}",
            f"WhatsApp: {customer_phone}",
            f"Cups: {cups}",
            f"Tea: {tea_type}",
            f"Flavours: {', '.join(flavour)}",
            f"Masala: {'Yes' if masala else 'No'}",
            f"Sugar: {sugar} tsp per cup",
            f"Milk: {milk}",
            f"Estimated: ₹{total:.1f}"
        ]
        summary_text = "\n".join(summary_lines)

        st.success(f"Thank you **{name}**! Your order is placed 🫖✨ We'll notify via WhatsApp.")
        st.balloons()

        # Owner notification
        owner_msg = f"""🆕 NEW CHAI ORDER!

{summary_text}

Please prepare soon. Cash/UPI on delivery for now."""
        ok_owner, msg_owner = send_whatsapp(OWNER_PHONE, owner_msg)
        if ok_owner:
            st.toast("Notified owner via WhatsApp", icon="✅")
        else:
            st.warning(f"Owner notification failed: {msg_owner}")

        # Customer confirmation
        cust_msg = f"""Hi *{name}*! 🫖✨

Your chai is confirmed!

{summary_text}

We'll get it ready soon. See you! ☕❤️
ChaiWala AI"""
        ok_cust, msg_cust = send_whatsapp(customer_phone, cust_msg)
        if ok_cust:
            st.success("Confirmation sent to your WhatsApp")
        else:
            st.error(f"Confirmation failed: {msg_cust}")

        # QR code
        qr_data = f"Order: {name} • {cups}× {tea_type} • ₹{total:.1f} • {datetime.datetime.now().strftime('%d-%b %H:%M')}"
        qr = qrcode.QRCode(version=1, box_size=6, border=4)
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#8B4513", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        st.image(buf, caption="Order Summary QR (share if needed)", width=180)

# ────────────────────────────────────────────────
#   ALWAYS-ON CHATBOT
# ────────────────────────────────────────────────
st.markdown("---")
st.subheader("🗣️ Talk to ChaiWala AI")
st.caption("Ask anything: menu, prices, custom chai ideas, payment (currently cash/UPI on delivery), chai facts... I'm here 24/7!")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "system", "content": """You are ChaiWala AI – a warm, fun, Delhi-style chai expert.
Use friendly desi language (mix Hindi-English naturally).
Menu info:
- Milk Tea / Masala Tea: ₹15 per cup
- Green Tea / Black Tea: ₹12 per cup
- Add-ons: Ginger/Cardamom/Tulsi ₹4 each, extra sugar ₹2/tsp/cup, masala option free
- Milk: Full Fat, Low Fat, Almond, None
- Cups: 1–20, sugar 0–5 tsp/cup
Payment: Cash or UPI on delivery for now (online coming soon)
Orders placed via the form above. Be helpful, keep replies short & tasty unless more detail asked.
Add fun chai facts or jokes sometimes!"""}
    ]

# Show chat history
for message in st.session_state.chat_history:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# User message
if user_msg := st.chat_input("Ask me anything about chai..."):
    if not groq_client:
        st.error("Chatbot not available – Groq API key missing")
    else:
        st.session_state.chat_history.append({"role": "user", "content": user_msg})
        with st.chat_message("user"):
            st.markdown(user_msg)

        with st.chat_message("assistant"):
            placeholder = st.empty()
            full_response = ""

            try:
                stream = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=st.session_state.chat_history,
                    temperature=0.75,
                    max_tokens=400,
                    stream=True
                )

                for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        full_response += chunk.choices[0].delta.content
                        placeholder.markdown(full_response + "▌")
                placeholder.markdown(full_response)

            except Exception as e:
                error_text = f"Oops! Thodi si dikkat ho gayi... ({str(e)})\nTry again?"
                placeholder.markdown(error_text)
                full_response = error_text

        st.session_state.chat_history.append({"role": "assistant", "content": full_response})

if st.button("Clear Chat History"):
    st.session_state.chat_history = [st.session_state.chat_history[0]]
    st.rerun()

st.caption("Test version • WhatsApp via Twilio Sandbox • Payments: cash/UPI on delivery for now")