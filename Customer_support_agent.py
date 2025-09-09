from agents import Agent, Runner, function_tool
from agent_config import model
from typing import Dict

faqs = {
    "return policy": "You can return items within 30 days of purchase as long as they are unused and in original packaging.",
    "shipping time": "Standard shipping takes 3–5 business days, express takes 1–2 days.",
    "shipping cost": "Shipping is free for orders above $50, otherwise a $5 fee applies.",
    "payment methods": "We accept credit/debit cards, PayPal, and Apple Pay.",
    "order tracking": "Track your order using the tracking link in your email or by providing your order ID here.",
    "warranty": "All products come with a 1-year warranty against manufacturing defects.",
    "support hours": "Customer support is available Monday–Friday, 9 AM to 6 PM."
}
order_db: Dict[str, Dict[str, str]] = {
    "123": {"status": "Shipped", "eta": "2-3 days", "carrier": "FastEx"},
    "456": {"status": "Processing", "eta": "5-7 days", "carrier": "LogiPak"},
    "789": {"status": "Delivered", "eta": "—", "carrier": "FastEx"},
    "101": {"status": "Pending Payment", "eta": "N/A", "carrier": "N/A"},
    "202": {"status": "Cancelled", "eta": "N/A", "carrier": "N/A"},
}

# isinstance()
@function_tool(
    is_enabled=lambda run_context, agent: "order_id" in run_context.input.lower(),
    failure_error_function=lambda e: f"Error retrieving order status: {str(e)}"
)
def order_status(order_id: str) -> str:
    """Fetch the order status from a simulated database."""
    if order_id not in order_db:
        raise ValueError("Order not found")
    return order_db.get(order_id, "I'm sorry, I don't have information on that order.")

@function_tool
def basic_FAQs(faq: str) -> str:
    return faqs.get(faq.lower(), "I'm sorry, I don't have information on that topic. Please contact support for further assistance.")


@function_tool
def complex_faqs(faqs: str) -> str:
    complex_faqs_dict = {
        "cancel order": "Orders can be canceled within 24 hours unless already shipped.",
        "change shipping address": "Shipping address can be changed before the order is shipped by contacting support.",
        "report damaged item": "Report damaged items within 7 days of receipt for a replacement or refund.",
        "technical issue": "For technical issues with the website or app, please provide details for assistance.",
        "bulk order": "For bulk orders, please contact our sales team for special pricing and arrangements."
    }
    return complex_faqs_dict.get(faqs.lower())

trigger_words = ["human", "agent", "representative", "support", "complex","angry", "complain", "worst", "hate", "stupid", "refund", "bad service", "upset"]

human_agent = Agent(
    name="HumanAgent",
    instructions="""
    You are a human agent who can assist with complex customer inquiries that require human judgment.
    Your task is to provide personalized assistance and resolve issues that cannot be handled by automated systems.
    Always ensure to maintain a polite and professional tone in your responses.
""",
    model=model,
    tools=[complex_faqs, order_status]
)

customer_support_agent = Agent(
    name="CustomerSupportAgent",
    instructions="""
    You are a customer support agent for an e-commerce platform.
    Your task is to assist customers with their inquiries regarding orders, returns, and product information.
    Provide clear and concise responses to customer questions.
""",
    model=model,
    tools=[basic_FAQs, order_status]
    
)

# @function_tool
# def guardrail(prompt: str) -> str:
#     if any(word in prompt.lower() for word in trigger_words) or not any(word in prompt.lower() for word in faqs.keys()):
#         return "escalate to human agent"
#     return "handle with automated system"

triage_agent = Agent(
    name="TriageAgent",
    instructions="""
     You are a triage agent.
    - If the user asks about order status, tracking, or shipping → handoff to CustomerSupportAgent.
    - If the user asks a FAQ (return policy, shipping time, warranty, etc.) → handoff to CustomerSupportAgent.
    - If the user query contains negative or complex words (angry, complain, refund, bad service, etc.)
      → escalate to HumanAgent.
    - If user query contains any of the human, agent, representative, support, complex, angry, complain, worst, hate, stupid, refund, bad service, upset
      words or is not found in the FAQs, you should escalate the conversation to human agent.
    Always choose the correct handoff.
""",
    model=model,
    # tools=[guardrail],
    handoffs=[customer_support_agent, human_agent]

)

prompt = input("Enter your prompt: ")
result = Runner.run_sync(triage_agent, prompt)
print(result.final_output)