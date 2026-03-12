# ChaiWala AI 🫖🤖

An AI-powered chai ordering web app built with **Streamlit** — perfect for small chai stalls, tea shops, or home businesses in India.

Customers can:
- Customize their chai order (type, cups, sugar level, masala, flavors, milk)
- Get a warm, desi-style AI description of their order (powered by Groq + Llama)
- Chat with an always-on AI assistant for menu questions, custom requests, chai facts, etc.
- Place order → receive instant WhatsApp confirmation (via Twilio sandbox)
- See a shareable QR code for the order summary

Payments are currently cash/UPI on delivery (Razorpay integration coming soon).


## Features

- Beautiful, mobile-friendly Streamlit interface
- Real-time Groq AI for order descriptions & chatbot
- WhatsApp notifications to customer & owner
- Order QR code generation
- Secure credential handling (no keys in code)
- Easy to run locally or deploy free on Streamlit Cloud

## Tech Stack

- **Frontend / App**: Streamlit
- **AI**: Groq (Llama-3.3-70b-versatile)
- **Messaging**: Twilio WhatsApp API (sandbox mode)
- **QR Code**: qrcode + Pillow
- **Secure secrets**: Streamlit secrets + os.getenv

## How to Run Locally

1. Clone the repo:
   ```bash
   git clone https://github.com/shivampython123/chaiwala-ai-app.git
   cd chaiwala-ai-app