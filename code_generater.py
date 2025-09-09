from agents import Agent, Runner, trace
from pydantic import BaseModel
from agent_config import model
import asyncio

project_idea_generator = Agent(
    name="ProjectIdeaGenerator",
    instructions="""
    You are an AI agent that generates creative and unique project ideas based on user input.
    Your task is to come up with a catchy and relevant idea for the project described by the user.
    Ensure that the idea is easy to remember and reflects the essence of the project.
""",
    model=model,
)

class ProjectIdeaChecker(BaseModel):
    is_feasible: bool  # Can it realistically be built?
    is_original: bool  # Is the idea novel or unique?
    matches_domain: bool  # Relevant to the intended field or topic?
    has_clear_goals: bool  # Is the idea well-defined?
    avoids_ethics_issues: bool  # No major ethical concerns?
    is_scalable: bool  # Can it be expanded or improved later?
    has_user_value: bool  # Will users find it useful or engaging?


project_idea_checker = Agent(
    name="ProjectIdeaChecker",
    instructions="""
    You are an AI agent that evaluates project ideas based on specific criteria.
    Your task is to assess the feasibility, originality, relevance, clarity, ethical considerations, scalability, and user value of the project idea provided by the user.
    Provide a detailed evaluation based on these criteria.
""",
    model=model,
    output_type=ProjectIdeaChecker
)    

projects_code_generator = Agent(
    name="ProjectsCodeGenerator",
    instructions="""
    You are an AI agent that generates code snippets based on project ideas and the given language by the user.

    Your task is to create functional and efficient code that aligns with the project idea described by the
    user. Ensure that the code is well-structured and follows best practices.
""",
    model=model,

)

async def main():
    prompt = input("Enter what type of project idea do you want: ")
    with trace("Project Idea Generation"):
       # 1. Generate Project Idea
       idea_result = await Runner.run(project_idea_generator, prompt)
       print(f"Generated Project Idea: {idea_result.final_output}")

       # 2. Check Project Idea
       check_result = await Runner.run(project_idea_checker, idea_result.final_output)


       # 3. Generate Project Code
       assert isinstance(check_result.final_output, ProjectIdeaChecker)
       if not all([
            check_result.final_output.is_feasible,
            check_result.final_output.is_original,
            check_result.final_output.matches_domain,
            check_result.final_output.has_clear_goals,
            check_result.final_output.avoids_ethics_issues,
            check_result.final_output.is_scalable,
            check_result.final_output.has_user_value
        ]):
          print("The project idea did not pass the evaluation criteria. Please try again with a different idea.")
          exit(0)


       print("The project idea passed the evaluation criteria. Generating code...")   

       # 4. Generate Code
       code_result = await Runner.run(projects_code_generator, idea_result.final_output)
       print(f"Generated Code Snippet: {code_result.final_output}")


if __name__ == "__main__":
    asyncio.run(main())