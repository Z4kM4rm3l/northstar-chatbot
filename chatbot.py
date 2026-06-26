import os
import google.generativeai as genai

# Configure Gemini
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash")

# Mock order data (Strictly as required by client)
ORDER_DATA = {
    "111": {"status": "Shipped", "message": "Your order #111 has been shipped and is arriving tomorrow! 🚚"},
    "222": {"status": "Processing", "message": "Your order #222 is currently processing and will ship within 24 hours. 📦"},
    "333": {"status": "Delivered", "message": "Your order #333 has been delivered! 🎉 Did you receive everything okay and matching your expectations?"},
}

# Return policy (Strictly as required by client)
RETURN_POLICY = (
    "Our return policy allows returns within 30 days of purchase. "
    "Items must be unused and in original packaging. "
    "To start a return, visit: https://northstargear.com/returns"
)

# Shipping info (Strictly as required by client)
SHIPPING_INFO = (
    "We offer two shipping options:\n"
    "• Standard Shipping: 3-5 business days\n"
    "• Expedited Shipping: 1-2 business days"
)

# Intent keywords
INTENT_KEYWORDS = {
    "order_tracking": ["order", "track", "tracking", "where is", "package", "shipment", "status", "order number"],
    "returns": ["return", "exchange", "refund", "send back", "return policy", "doesn't fit"],
    "product_recommendation": ["recommend", "suggestion", "choose", "looking for", "camping", "hiking", "gear", "apparel"],
    "human_handoff": ["human", "agent", "person", "representative", "live agent", "speak to someone"],
    "shipping": ["shipping", "how long", "delivery time", "when will"],
    "small_talk": ["how are you", "what's up", "sup", "how's it going", "good morning", "good afternoon", "good evening", "thanks", "thank you", "cool", "awesome", "great"]
}


def detect_intent(message: str) -> str:
    """Detect user intent using Gemini first, keywords as fallback."""

    prompt = f"""You are an intent classifier for an outdoor gear e-commerce support chatbot.
Classify the following message into exactly one of these intents:
- order_tracking
- returns
- product_recommendation
- human_handoff
- shipping
- small_talk
- unknown

Message: "{message}"

Respond with only the intent label, nothing else. If you are not confident, respond with "unknown"."""

    try:
        response = model.generate_content(prompt)
        intent = response.text.strip().lower()
        if intent in INTENT_KEYWORDS or intent == "unknown":
            return intent
    except Exception:
        pass

    # Keyword fallback if Gemini fails or returns unexpected value
    message_lower = message.lower()
    scores = {intent: 0 for intent in INTENT_KEYWORDS}
    for intent, keywords in INTENT_KEYWORDS.items():
        for keyword in keywords:
            if keyword in message_lower:
                scores[intent] += 1

    best_intent = max(scores, key=scores.get)
    if scores[best_intent] > 0:
        return best_intent

    return "unknown"


def get_recommendation(history: list) -> str:
    """Generate a contextual product recommendation using conversation history."""
    history_text = "\n".join([
        f"{msg['role'].replace('assistant', 'North Star')}: {msg['content']}"
        for msg in history[-8:]
    ])
    prompt = f"""You are North Star, a friendly, outdoorsy support bot helping a customer find gear or apparel.

Based on the full conversation history below, provide a warm, specific, and personalized product category recommendation in 2-3 sentences. 
Reference what the customer actually told you — their activity, climate, group, or goals. 
Do not recommend specific brands. Be enthusiastic and outdoorsy in tone.

Conversation history:
{history_text}

North Star:"""
    try:
        response = model.generate_content(prompt)
        return response.text.strip() + "\n\nIs there anything else I can help you with today? 🏕️"
    except Exception:
        return (
            "Based on what you've shared, I'd recommend starting with moisture-wicking base layers, "
            "a reliable shelter system, and sun protection essentials for your trip! 🏕️\n\n"
            "Is there anything else I can help you with today?"
        )


class NorthStarChatbot:
    def __init__(self):
        self.sessions = {}

    def get_session(self, session_id: str) -> dict:
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "state": "greeting",
                "history": [],
                "awaiting": None,
            }
        return self.sessions[session_id]

    def process_message(self, session_id: str, user_message: str) -> str:
        session = self.get_session(session_id)

        if session.get("state") == "human_handoff_active":
            # Use intent detection to allow natural exit from handoff state
            exit_intent = detect_intent(user_message)
            if exit_intent in ["order_tracking", "returns", "shipping", "product_recommendation", "small_talk"] or \
               any(word in user_message.lower() for word in ["exit", "main menu", "back", "cancel", "nevermind", "home"]):
                session["state"] = "main"
                return (
                    "No problem! Taking you back to the main menu. 🏔️\n\n"
                    "I can help you with:\n"
                    "• 📦 Tracking your order\n"
                    "• 🔄 Returns & exchanges\n"
                    "• 🧭 Gear recommendations\n"
                    "• 🚚 Shipping information\n\n"
                    "What can I help you with today?"
                )
            return "A live guide will be with you shortly. 🏕️ Your conversation history has been saved and shared with the agent."

        session["history"].append({"role": "user", "content": user_message})
        response = self._handle_message(session, user_message)
        session["history"].append({"role": "assistant", "content": response})
        return response

    def _handle_message(self, session: dict, user_message: str) -> str:
        msg_lower = user_message.lower()

        intent = detect_intent(user_message)

        # ==========================================
        # 1. AWAITING STATES FIRST
        # ==========================================
        if session["awaiting"] == "order_number":
            if any(word in msg_lower for word in ["human", "agent", "person", "talk to", "live agent", "representative"]):
                session["awaiting"] = None
                session["state"] = "human_handoff_active"
                return (
                    "Of course! Let me get a real person on the line for you. 🙋\n\n"
                    "🔄 **Transferring to Live Agent...**\n"
                    "An agent will be with you shortly and will have your full conversation history. "
                    "Average wait time is under 2 minutes."
                )
            session["awaiting"] = None
            session["state"] = "main"
            clean_num = user_message.strip().lstrip("#")
            if clean_num == "333":
                session["awaiting"] = "post_delivery_followup"
                return ORDER_DATA["333"]["message"]
            elif clean_num in ORDER_DATA:
                return ORDER_DATA[clean_num]["message"]
            else:
                return f"I couldn't find order #{clean_num}. Please double-check your order number and try again."

        if session["awaiting"] == "post_delivery_followup":
            session["awaiting"] = None
            session["state"] = "main"
            if any(word in msg_lower for word in ["no", "issue", "problem", "missing", "damaged", "wrong", "bad"]):
                session["state"] = "human_handoff_active"
                return (
                    "Oh no, I'm sorry to hear that! Missing or damaged items is something we want to "
                    "resolve for you right away. 😟\n\n"
                    "🔄 **Transferring to Live Agent...**\n"
                    "I'm connecting you with a team member now who can look into this personally and make it right. "
                    "Your full conversation history has been saved and shared with them."
                )
            return "Awesome! So glad everything arrived safely. Let me know if you need any gear suggestions or have any other questions. Happy trails! 🌲"

        if session["awaiting"] == "rec_q1":
            session["awaiting"] = "rec_q2"
            return "Got it! What kind of climate or weather conditions are you expecting out there? 🌦️"

        if session["awaiting"] == "rec_q2":
            session["awaiting"] = None
            session["state"] = "main"
            return get_recommendation(session["history"])

        # ==========================================
        # 2. MANDATORY WELCOME GREETING
        # ==========================================
        if session["state"] == "greeting":
            session["state"] = "main"
            return (
                "Hey there, adventurer! 🏔️ I'm **North Star**, your outdoor gear support bot.\n"
                "I can help you with:\n\n"
                "• 📦 Tracking your order\n"
                "• 🔄 Returns & exchanges\n"
                "• 🧭 Gear recommendations\n"
                "• 🚚 Shipping information\n\n"
                "What can I help you with today?"
            )

        # ==========================================
        # 2b. RECOMMENDATION ACTIVE STATE
        # ==========================================
        if session.get("state") == "recommendation_active":
            if any(word in msg_lower for word in ["human", "agent", "person", "talk to", "live agent", "representative"]):
                session["state"] = "human_handoff_active"
                return (
                    "Of course! Let me get a real person on the line for you. 🙋\n\n"
                    "🔄 **Transferring to Live Agent...**\n"
                    "An agent will be with you shortly and will have your full conversation history. "
                    "Average wait time is under 2 minutes."
                )

            history_text = "\n".join([
                f"{msg['role'].replace('assistant', 'North Star')}: {msg['content']}"
                for msg in session["history"][-8:]
            ])
            prompt = f"""You are North Star, a friendly, outdoorsy support bot helping a customer find gear or apparel.

The customer is continuing a product recommendation conversation. Based on everything they've shared, 
either ask one more clarifying question if needed, or provide a warm personalized recommendation 
referencing their specific situation. Do not recommend specific brands. Be enthusiastic and outdoorsy.

Conversation history:
{history_text}

North Star:"""
            try:
                response = model.generate_content(prompt)
                return response.text.strip()
            except Exception:
                return get_recommendation(session["history"])

        # ==========================================
        # 3. GLOBAL INTENT ROUTING
        # ==========================================
        if intent == "order_tracking":
            for word in user_message.split():
                clean = word.strip("#.,").strip()
                if clean.isdigit():
                    if clean == "333":
                        session["awaiting"] = "post_delivery_followup"
                        session["state"] = "main"
                        return ORDER_DATA["333"]["message"]
                    elif clean in ORDER_DATA:
                        session["state"] = "main"
                        return ORDER_DATA[clean]["message"]
            session["awaiting"] = "order_number"
            return "Sure thing! What is your order number? 🔍"

        elif intent == "returns":
            return f"No problem! Here's our return policy:\n\n📋 {RETURN_POLICY}\n\nAnything else I can help with?"

        elif intent == "shipping":
            return f"Here's how our packages travel:\n\n🚚 {SHIPPING_INFO}\n\nWhat else can I look up for you?"

        elif intent == "product_recommendation":
            session["state"] = "recommendation_active"
            history_text = "\n".join([
                f"{msg['role'].replace('assistant', 'North Star')}: {msg['content']}"
                for msg in session["history"][-6:]
            ])
            prompt = f"""You are North Star, a friendly, outdoorsy support bot helping a customer find gear or apparel.

CRITICAL TASK:
Review the conversation history. If the customer has NOT specified their exact activity, environment, or specific gear needs yet, you MUST ask ONE highly relevant clarifying question (e.g., "Are you backpacking light or car camping?", "What kind of climate are you facing?", "Are you looking for clothing or camp gear?"). 

If they have already provided those details across the last 1-2 messages, provide a concise product category recommendation (2-3 sentences max) matching their needs. Do not recommend specific brands. Keep your tone concise, rugged, and enthusiastic.

Conversation history:
{history_text}

North Star:"""
            try:
                response = model.generate_content(prompt)
                return response.text.strip()
            except Exception:
                session["awaiting"] = "rec_q1"
                return "I'd love to help you find the right setup! 🏔️ What specific outdoor activity are you planning next (e.g., hiking, camping, backpacking)?"

        elif intent == "human_handoff":
            session["state"] = "human_handoff_active"
            return (
                "Of course! Let me get a real person on the line for you. 🙋\n\n"
                "🔄 **Transferring to Live Agent...**\n"
                "An agent will be with you shortly and will have your full conversation history. "
                "Average wait time is under 2 minutes."
            )

        elif intent == "small_talk":
            prompt = f"""You are North Star, a friendly outdoor gear support bot.
The customer said: "{user_message}"
Respond warmly and briefly in 1-2 sentences, then naturally guide them back to what you can help with: order tracking, returns, gear recommendations, or shipping. Be outdoorsy and friendly."""
            try:
                response = model.generate_content(prompt)
                return response.text.strip()
            except Exception:
                return "Doing great and ready to help you gear up for your next adventure! 🏔️ What can I help you with today?"

        # ==========================================
        # 4. STANDARD FALLBACK HANDLING
        # ==========================================
        return "I didn't quite catch that. Try asking about tracking an order, returns, shipping, or gear recommendations! 🧭"


# Global chatbot instance
chatbot = NorthStarChatbot()