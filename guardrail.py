from pydantic import BaseModel
from agents import (
    Agent,
    GuardrailFunctionOutput,
    OutputGuardrailTripwireTriggered,
    RunContextWrapper,
    Runner,
    TResponseInputItem,
    output_guardrail,
)
from agent_config import model
import asyncio
from tool import add_numbers, get_weather
class MessageOutput(BaseModel): 
    response: str

class MathOutput(BaseModel): 
    reasoning: str
    is_math: bool

output_agent = Agent(
       "InputGuardrailAgent",
        instructions="Check and verify if input is related to math",
        model=model,
        output_type=MathOutput,
    )


@output_guardrail
async def math_guardrail(
    ctx: RunContextWrapper, agent: Agent, output_data: str | list[TResponseInputItem]
) -> GuardrailFunctionOutput:
    # Run your guardrail-checking agent
    result = await Runner.run(output_agent, output_data, context=ctx.context)

    return GuardrailFunctionOutput(
        output_info=result.final_output,
        tripwire_triggered=not result.final_output.is_math,
    )


math_agent = Agent(
    name="MathAgent",
    instructions="Perform mathematical operations",
    model=model,
    output_guardrails=[math_guardrail],
    tools=[add_numbers, get_weather]
)

async def main():
    try:
        # a = 10/0
        msg = input("Enter you question : ")
        result = await Runner.run(math_agent, msg)
        print(f"\n\n final output : {result.final_output}")
    except OutputGuardrailTripwireTriggered as ex:
        print("Error : invalid prompt")


asyncio.run(main())
