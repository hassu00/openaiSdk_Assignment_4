from agents import Agent, Runner, function_tool, OutputGuardrailResult, RunContextWrapper, OutputGuardrail, GuardrailFunctionOutput, trace, Session, SQLiteSession, OutputGuardrailTripwireTriggered
from agent_config import model
from agents import enable_verbose_stdout_logging, TResponseInputItem, input_guardrail, InputGuardrailTripwireTriggered
from typing import Dict
from pydantic import BaseModel


session = SQLiteSession(db_path="memory.db",session_id="agent01")

# enable_verbose_stdout_logging()
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
    is_enabled=True,
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
        "bulk order": "For bulk orders, please contact our sales team for special pricing and arrangements.",
        "refund process": "Refunds are processed within 5-7 business days after we receive the returned item.",
         "return policy": "You can return items within 30 days of purchase as long as they are unused and in original packaging.",
    }
    return complex_faqs_dict.get(faqs.lower())

class GuardrailInput(BaseModel):
    reasoning: str
    is_about_order: bool
    
input_checker = Agent(
    name="InputChecker",
    instructions="""
    You are an input checker agent.
    - Check if the user input is not about order status, tracking, or shipping.
    

    """,
    output_type=GuardrailInput,
    model=model,
  
)
@input_guardrail
def input_guardrail_function(context = RunContextWrapper[None], agent: Agent, input: str | list[TResponseInputItem]) -> GuardrailFunctionOutput:
    """Check if the input is about order status."""
    result = Runner.run(input_checker, input)
    final_output = result.final_output_as(GuardrailInput)
    return GuardrailFunctionOutput(
        output_info={"reasoning": final_output.reasoning, "is_about_order": final_output.is_about_order},
        tripwire_triggered= not final_output.is_about_order,
    )

trigger_words = ["human", "agent", "representative", "support", "complex","angry", "complain", "worst", "hate", "stupid", "refund", "bad service", "upset"]

human_agent = Agent(
    name="HumanAgent",
    instructions="""
     You are a human support representative. 
    - When the customer is upset, dissatisfied, or asks about returns/refunds, give them the actual return/refund policy and guide them step by step.  
    - Do NOT say "I will transfer you" or "I cannot help".  
    - Always answer directly, clearly, and politely, as if you are the final support person.  
    """,
    model=model,
    tools=[complex_faqs, order_status]
)

def should_escalate(user_input: str) -> bool:
    return any(word in user_input.lower() for word in trigger_words) or user_input.lower() not in faqs

@function_tool
def guardrail(prompt: str) -> str:
    # Escalate if trigger words are found OR query not in FAQs
    if any(word in prompt.lower() for word in trigger_words) or prompt.lower() not in faqs:
        return "escalate"
    return "handle"



from agents.guardrail import output_guardrail, GuardrailFunctionOutput

@output_guardrail
async def escalation_guardrail(context, agent, output: str) -> GuardrailFunctionOutput:
    triggers = [
        "not able to process",
        "I don't have information",
        "contact support",
        "unfortunately",
        "human", "agent", "representative", "support",
        "complex", "angry", "complain", "worst",
        "hate", "stupid", "refund", "bad service", "upset"
    ]

    if any(t in output.lower() for t in triggers):
        # Escalate to human agent
        result = await Runner.run(human_agent, output, session=session)
        return GuardrailFunctionOutput(
            output_info={"escalated_output": result.final_output},
            tripwire_triggered=True,
        )

    # Safe → no escalation
    return GuardrailFunctionOutput(
        output_info={"safe_output": output},
        tripwire_triggered=False,
    )

customer_support_agent = Agent(
    name="CustomerSupportAgent",
    instructions="""
    You are a customer support agent for an e-commerce platform.
    Your task is to assist customers with their inquiries regarding orders, returns, and product information.
    Provide clear and concise responses to customer questions.
    Provide the users the FAQs that I have given you.
    Use the provided tools to fetch order status or answer FAQs when necessary.
""",
    model=model,
    tools=[basic_FAQs, order_status],
    handoffs=[human_agent],
    handoff_description="""
    Escalate to HumanAgent if the guardrail tool says "escalate".
    """,
    output_guardrails=[escalation_guardrail],
    # handoff_description="""
    # - Escalate to HumanAgent for complex issues or if the customer is dissatisfied.
    # - If the user query contains negative or complex words (angry, complain, refund, bad service, etc.)
    #    → escalate to HumanAgent.
    # - If user query contains any of the human, agent, representative, support, complex, angry, complain, worst, hate, stupid, refund, bad service, upset words or is not found in the FAQs, you should escalate the conversation to human agent.
    # Always choose the correct handoff.
    # """,
)


# triage_agent = Agent(
#     name="TriageAgent",
#     instructions="""
#      You are a triage agent.
#     - If the user asks about order status, tracking, or shipping → handoff to CustomerSupportAgent.
#     - If the user asks a FAQ (return policy, shipping time, warranty, etc.) → handoff to CustomerSupportAgent.
#     - If the user query contains negative or complex words (angry, complain, refund, bad service, etc.)
#       → escalate to HumanAgent.
#     - If user query contains any of the human, agent, representative, support, complex, angry, complain, worst, hate, stupid, refund, bad service, upset
#       words or is not found in the FAQs, you should escalate the conversation to human agent.
#     Always choose the correct handoff.
# """,
#     model=model,
#     # tools=[guardrail],
#     handoffs=[customer_support_agent, human_agent]

  
            # )

async def main():
    try:
        prompt = input("Enter your prompt: ")
        result = await Runner.run(customer_support_agent, prompt, session=session)
        print("Bot Response:", result.final_output)
    except (OutputGuardrailTripwireTriggered, InputGuardrailTripwireTriggered) as e:
        if isinstance(e, InputGuardrailTripwireTriggered):
            print("plz ask about order status,like tracking, or shipping.")
        elif isinstance(e, OutputGuardrailTripwireTriggered):
            result = await Runner.run(human_agent, prompt, session=session)
            print("Escalated Bot Response:", result.final_output)

        
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())       