import streamlit as st
from groq import Groq
import qrcode
from PIL import Image
import io
from twilio.rest import Client
import os
import datetime
import re

# ────────────────────────────────────────────────
#   SECURE CREDENTIALS
# ────────────────────────────────────────────────
GROQ_API_KEY    = st.secrets.get("GROQ_API_KEY",    os.getenv("GROQ_API_KEY", ""))
TWILIO_SID      = st.secrets.get("TWILIO_ACCOUNT_SID", os.getenv("TWILIO_ACCOUNT_SID", ""))
TWILIO_TOKEN    = st.secrets.get("TWILIO_AUTH_TOKEN",  os.getenv("TWILIO_AUTH_TOKEN", ""))
TWILIO_FROM     = "whatsapp:+14155238886"
OWNER_PHONE     = st.secrets.get("OWNER_PHONE",     os.getenv("OWNER_PHONE", "+917987748574"))

if not GROQ_API_KEY:
    st.error("GROQ_API_KEY missing → AI features disabled")
if not TWILIO_SID or not TWILIO_TOKEN:
    st.warning("Twilio credentials missing → WhatsApp notifications disabled")

groq_client   = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
twilio_client = Client(TWILIO_SID, TWILIO_TOKEN) if TWILIO_SID and TWILIO_TOKEN else None

# ────────────────────────────────────────────────
#   HELPERS
# ────────────────────────────────────────────────
def normalize_phone(raw: str) -> str | None:
    digits = re.sub(r'\D', '', str(raw or ""))
    if len(digits) == 10:
        return "+91" + digits
    if len(digits) == 12 and digits.startswith("91"):
        return "+" + digits
    if digits.startswith("91") and 10 <= len(digits) <= 12:
        return "+91" + digits[-10:]
    if raw and raw.startswith("+") and len(digits) >= 10:
        return "+" + digits
    return None

def send_whatsapp(to_phone: str, body: str) -> tuple[bool, str]:
    if not twilio_client:
        return False, "Twilio not configured"
    to_norm = normalize_phone(to_phone)
    if not to_norm:
        return False, "Invalid phone number"
    to_whatsapp = f"whatsapp:{to_norm}"
    try:
        msg = twilio_client.messages.create(
            body=body,
            from_=TWILIO_FROM,
            to=to_whatsapp
        )
        return True, f"Sent (SID: {msg.sid})"
    except Exception as e:
        return False, str(e)

# ────────────────────────────────────────────────
#   PAGE CONFIG + STYLING
# ────────────────────────────────────────────────
st.set_page_config(
    page_title="ChaiWala • Fresh Chai Delivered",
    page_icon="🫖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    .main .block-container {padding-top: 1.2rem; padding-bottom: 2rem; background-color: #ffffff;}
    .stButton > button {border-radius: 10px; font-weight: 600; transition: all 0.25s;}
    
    button[kind="primary"], .stButton > button[kind="primary"] {
        background-color: #E84C2E !important;
        color: white !important;
        border: none;
    }
    button[kind="primary"]:hover, .stButton > button[kind="primary"]:hover {
        background-color: #D63E20 !important;
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(214, 62, 32, 0.3);
    }
    
    [data-testid="stColumn"]:nth-child(2) {
        background: #FFF8F2;
        border-left: 1px solid #EDEDED;
        padding: 1.2rem 1.4rem;
        border-radius: 10px;
        min-height: 82vh;
    }
    
    .stAlert.info {
        background-color: #FFE0CC !important;
        border: 1px solid #FF8533 !important;
        border-radius: 12px !important;
        padding: 1.3rem !important;
        box-shadow: 0 3px 10px rgba(255, 133, 51, 0.18) !important;
        color: #111111 !important;
    }
    
    div.stMarkdown > div > p,
    div.stMarkdown > div > h4,
    div.stMarkdown blockquote {
        background-color: #FFF0E0 !important;
        padding: 1.3rem 1.4rem !important;
        border-radius: 10px !important;
        border-left: 5px solid #FF6B35 !important;
        margin: 1.2rem 0 !important;
        box-shadow: 0 2px 8px rgba(255, 107, 53, 0.12) !important;
        color: #111111 !important;
    }
    
    .success-box {
        background-color: #FFF0E0;
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 6px solid #FF6B35;
        margin: 1.5rem 0;
        box-shadow: 0 4px 12px rgba(255, 107, 53, 0.15);
        color: #111111;
    }
    
    .chat-header {
        font-size: 1.3rem;
        font-weight: 700;
        color: #E84C2E;
        margin-bottom: 1.1rem;
    }
    
    hr {border-color: #E0E0E0; margin: 1.5rem 0;}
    </style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
#   LAYOUT
# ────────────────────────────────────────────────
main_col, chat_col = st.columns([7, 3])

with main_col:
    st.markdown(
        "<h1 style='color: #E84C2E; margin-bottom: 0.5rem;'>🫖 ChaiWala • Tapri-Style Chai, Delivered Fast!</h1>",
        unsafe_allow_html=True
    )
    st.caption("Fresh • Custom masala • Cash / UPI on delivery • Delhi NCR")

    with st.expander("📱 WhatsApp Updates – Required for tracking", expanded=True):
        st.markdown("""
        1. Open WhatsApp  
        2. Send **join dozen-huge** to **+14155238886**  
        3. Wait for confirmation reply  
        4. Enter the same number below  
        """)

    with st.form("chai_order_form"):
        st.subheader("Build Your Chai ☕")

        c1, c2 = st.columns([5, 4])

        with c1:
            name = st.text_input("Your Name", placeholder="Rahul Verma", max_chars=40).strip()
            phone_raw = st.text_input("WhatsApp Number", placeholder="7987748574 or +917987748574")
            cups = st.number_input("Cups", min_value=1, max_value=20, value=1, step=1)

            tea_type = st.radio("Tea Type", ["Milk Tea", "Masala Tea", "Green Tea", "Black Tea"], horizontal=True)
            masala = st.checkbox("Extra Masala (free)", value=True)
            flavour = st.multiselect("Extra Tadka", ["Ginger", "Cardamom", "Tulsi", "None"], default=["None"])
            sugar = st.slider("Sugar (tsp per cup)", 0, 5, 2)
            milk = st.selectbox("Milk Type", ["Full Fat", "Low Fat", "Almond", "None"])

            # Order Type
            order_mode = st.radio(
                "Order Type",
                ["Delivery", "Dine-in / Pickup"],
                horizontal=True,
                index=0,
                help="Dine-in / Pickup available only at select ChaiWala locations"
            )

            # Address field only appears for Delivery
            delivery_address = ""
            if order_mode == "Delivery":
                st.markdown("### Delivery Details")
                delivery_address = st.text_area(
                    "Full Delivery Address *",
                    placeholder="Flat no, Building name, Street, Landmark, Area, Delhi - Pincode",
                    height=100,
                    help="Please include flat number, landmark and pincode for fast delivery"
                )

        with c2:
            st.markdown("#### Price Preview")

            base_price   = 12 if tea_type in ["Green Tea", "Black Tea"] else 15
            flavour_cost = len([f for f in flavour if f != "None"]) * 4
            sugar_cost   = sugar * 2
            subtotal     = (base_price + flavour_cost + sugar_cost) * cups
            gst_amount   = subtotal * 0.18
            total        = round(subtotal + gst_amount, 1)

            st.info(f"""
**Per cup**  
Base → ₹{base_price}  
Flavours → ₹{flavour_cost}  
Sugar → ₹{sugar_cost}  
Masala → Free  

**Subtotal** → ₹{subtotal:.1f}  
**GST 18%** → ₹{gst_amount:.1f}  
**Total** → **₹{total:.1f}**
            """)

            if st.form_submit_button("Get AI Description", use_container_width=True):
                if name and phone_raw and groq_client:
                    with st.spinner("Brewing your special message..."):
                        addr_part = f"Address: {delivery_address.strip()}" if order_mode == "Delivery" and delivery_address.strip() else ""
                        prompt = f"""
Greet {name} like a true Delhi chai-wala bhaiya — warm, funny, full desi vibe.
Describe this chai order excitedly in Hindi-English mix.
Add one short useful chai tip or fun fact.
Order: {cups} cups of {tea_type}, {'with masala' if masala else 'no masala'},
flavours: {', '.join(flavour)}, {sugar} tsp sugar per cup, milk: {milk}
Mode: {order_mode}
{addr_part}
Keep it short & tasty (~100-140 words).
                        """
                        try:
                            resp = groq_client.chat.completions.create(
                                model="llama-3.3-70b-versatile",
                                messages=[{"role": "user", "content": prompt}],
                                temperature=0.82,
                                max_tokens=180
                            )
                            st.markdown("**ChaiWala AI says:**")
                            st.markdown(resp.choices[0].message.content.strip())
                        except Exception as e:
                            st.error(f"AI error: {e}")

        submitted = st.form_submit_button("PLACE ORDER 🛒", type="primary", use_container_width=True)

    if submitted:
        norm_phone = normalize_phone(phone_raw)
        errors = []

        if not name.strip():
            errors.append("Name is required")
        if not norm_phone:
            errors.append("Valid WhatsApp number is required")
        if order_mode == "Delivery":
            if not delivery_address.strip():
                errors.append("Delivery address is required when choosing Delivery mode")

        if errors:
            for err in errors:
                st.error(err)
        elif not twilio_client:
            st.error("WhatsApp service unavailable right now")
        else:
            summary_lines = [
                f"**Order #{datetime.datetime.now().strftime('%H%M%S')}**",
                f"Customer: {name}",
                f"WhatsApp: {norm_phone}",
                f"─────",
                f"{cups} × {tea_type}",
                f"Masala: {'Yes' if masala else 'No'}",
                f"Flavours: {', '.join(f for f in flavour if f != 'None') or 'None'}",
                f"Sugar: {sugar} tsp/cup",
                f"Milk: {milk}",
                f"─────",
                f"Mode: {order_mode}",
            ]
            if order_mode == "Delivery" and delivery_address.strip():
                summary_lines.append(f"Address: {delivery_address.strip()}")
            summary_lines += [f"Total: ₹{total:.1f} (incl. GST)"]

            summary_text = "\n".join(summary_lines)

            st.balloons()
            st.markdown(
                f'<div class="success-box"><h3>Order Placed Successfully! 🫖✨</h3>'
                f'<pre>{summary_text}</pre>'
                f'<p>Our team will confirm shortly via WhatsApp. Thank you for choosing ChaiWala!</p></div>',
                unsafe_allow_html=True
            )

            # Owner message
            owner_msg = f"""🔔 NEW CHAI ORDER #{datetime.datetime.now().strftime('%H%M%S')} 🔔

{summary_text}

Preparation Priority: {'High - Delivery' if order_mode == 'Delivery' else 'Medium - Dine-in/Pickup'}
Payment: Cash / UPI on arrival

Please prepare as soon as possible.
Thank you! ☕🔥
ChaiWala Team"""

            send_whatsapp(OWNER_PHONE, owner_msg)

            # Customer confirmation
            cust_msg = f"""नमस्ते *{name}* ji! 🫖✨

Your chai order is confirmed!

{summary_text}

{'We will deliver fresh to your address shortly. Stay tuned!' if order_mode == 'Delivery' else 'Please come to the stall for pickup / enjoy dine-in at your convenience.'}

Brewing just for you... ☕❤️

ChaiWala Team
(Updates via WhatsApp)"""

            send_whatsapp(phone_raw, cust_msg)

            # QR code
            qr_data = f"ChaiWala Order • {name} • {cups}×{tea_type} • ₹{total:.1f} • {order_mode}"
            qr = qrcode.QRCode(version=1, box_size=5, border=4)
            qr.add_data(qr_data)
            qr.make(fit=True)
            img = qr.make_image(fill_color="#E84C2E", back_color="white")
            buf = io.BytesIO()
            img.save(buf, "PNG")
            buf.seek(0)
            st.image(buf, caption="Order QR – show on arrival / delivery", width=160)

with chat_col:
    st.markdown('<div class="chat-header">🗣️ ChaiWala AI</div>', unsafe_allow_html=True)
    st.caption("Ask menu, prices, custom ideas, chai facts...")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [{
            "role": "system",
            "content": """You are ChaiWala AI – warm, funny Delhi-style chai bhaiya.
Use natural desi Hindi-English mix.
Menu:
- Milk Tea / Masala Tea: ₹15/cup
- Green / Black Tea: ₹12/cup
Add-ons: Ginger/Cardamom/Tulsi ₹4 each, extra sugar ₹2/tsp/cup, masala free
Milk: Full Fat, Low Fat, Almond, None
Payment: Cash / UPI on delivery
Order types: Delivery or Dine-in/Pickup
Keep replies short, tasty & helpful. Add chai facts/jokes sometimes."""
        }]

    chat_container = st.container(height=520, border=True)

    with chat_container:
        for msg in st.session_state.chat_history[1:]:
            if msg["role"] != "system":
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

    if len(st.session_state.chat_history) > 24:
        st.session_state.chat_history = [st.session_state.chat_history[0]] + st.session_state.chat_history[-22:]

    user_input = st.chat_input("Ask anything about chai...", key="right_chat")

    if user_input and groq_client:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with chat_container:
            with st.chat_message("user"):
                st.markdown(user_input)

        with chat_container:
            with st.chat_message("assistant"):
                placeholder = st.empty()
                full = ""
                try:
                    stream = groq_client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=st.session_state.chat_history,
                        temperature=0.78,
                        max_tokens=320,
                        stream=True
                    )
                    for chunk in stream:
                        if chunk.choices[0].delta.content is not None:
                            full += chunk.choices[0].delta.content
                            placeholder.markdown(full + "▌")
                    placeholder.markdown(full)
                except Exception as e:
                    placeholder.markdown(f"Oops bhai! Thodi dikkat... ({str(e)})")

        st.session_state.chat_history.append({"role": "assistant", "content": full})
        st.rerun()

    if st.button("Clear Chat", use_container_width=True):
        st.session_state.chat_history = [st.session_state.chat_history[0]]
        st.rerun()

st.caption("ChaiWala • Twilio Sandbox • Delhi vibes only • v1.0 • 2026")
