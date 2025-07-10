import openai
from prompts.prompts import Tutor_prompt, Classify_prompt
import os
import requests
from langgraph.graph import MessagesState, StateGraph, START, END
from langchain_core.tools import tool
from langgraph.types import Command, interrupt
from langchain_openai import ChatOpenAI
from typing import TypedDict
from typing import List, Dict, Any
from dotenv import load_dotenv
import json
from utils.web_search import serpapi_search

load_dotenv()

math_solver_api = os.getenv('MATH_SOLVER')
math_tutor_api = os.getenv('MATH_TUTOR')

#define langgraph state
class ChatState(TypedDict):
    messages:List[Dict[str, Any]] = []
    ground_truth: str = ""
    problem: str = ""
    student_solution: str = ""
    student_get_it_right: int = 0
    web_query: str = ""

#define langgraph tool
@tool 
def web_search(query: str):
    """Find some information in the web"""
    result = serpapi_search(query)
    return result

@tool
def get_solver(problem:str):
    """Get solution for a math problem"""
    payload = {"prompt": problem}
    response = requests.post(math_solver_api, json=payload)
    result = response.json()
    return result.get('response')


@tool # để có thể sử dụng được invoke
def get_tutor_response(history_chat: list, problem: str, ground_truth: str):
    """Get tutor response """
    def create_diaglouge(history_chat):
        res = ""
        for message in history_chat:
            if message['role'] == "user":
                res += f"Student: {message['content']}\n"
            else:
                res += f"Teacher: {message['content']}\n"

        return res
    dialouge = create_diaglouge(history_chat[1:])
    user_prompt = f"""
        Problem: {problem}
        Ground truth solution: {ground_truth}
        Dialogue_history: {dialouge}
    """
    print("+++User prompt:", user_prompt)
    payload = {"prompt": user_prompt, "language": "Tiếng Việt"}

    response = requests.post(math_tutor_api, json=payload)
    result = response.json()
    print(result)
    return result.get('response')

from langchain.chat_models import init_chat_model

model = init_chat_model("openai:gpt-4o-mini", temperature=0.4)

model = model.bind_tools([get_solver, get_tutor_response])

classify_client = openai.OpenAI()

def identify_intent(state: ChatState):
    messages = state["messages"]
    problem = state['problem']
    ground_truth = state["ground_truth"]
    student_solution = state["student_solution"]
    student_get_it_right = state["student_get_it_right"]
    last_message = messages[-1]["content"]
    # print("Messages: ",last_message)
    response = classify_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": Classify_prompt(problem, student_solution, ground_truth, last_message)},
            ]
    )
    # print("Extraction: ", response)
    result = json.loads(response.choices[0].message.content)
    # print("Extraction: ", result)
    if problem == "" and result["problem"] != "":
        state['problem'] = result['problem']
    if state['student_solution'] == "":
        state['student_solution'] = result['student_solution']
    if state['student_get_it_right'] == 0:
        state['student_get_it_right'] = result['student_get_it_right']
    if state['web_query'] == "":
        state['web_query'] = result['web_query']
    return state

def which_tool(state: ChatState): #conditional edge
    messages = state["messages"]
    problem = state['problem']
    ground_truth = state["ground_truth"]
    student_solution = state["student_solution"]
    student_get_it_right = state["student_get_it_right"]
    last_message = messages[-1]["content"]
    web_query = state['web_query']
    typee = ""
    if web_query:
        return 'web_search'
    if problem == "":
        return "call_general_chat"
    if problem != "" and ground_truth == "":
        return 'solver'
    if problem != "" and student_solution == "":
        return "call_general_chat"
    if problem != "" and student_solution != "" and student_get_it_right == 0:
        return "tutor"
    return "call_general_chat"
    

def call_general_chat(state):
    messages = state["messages"]
    response = model.invoke(messages)
    messages.append({"role": "assistant", "content": response.content})
    state["messages"] = messages
    return state

def web_searchh(state):
    web_query = state['web_query']
    response = web_search(web_query)
    state["messages"].append({"role": "assistant", "content": response})
    return state

def solver(state: ChatState):
    problem = state['problem']
    ground_truth = get_solver.invoke({"problem": problem})
    state['ground_truth'] = ground_truth
    # state.messagesappend({"role": "assistant", "content": f"Here is the solution: {ground_truth}"})
    return state

def tutor(state: ChatState):
    problem = state['problem']
    ground_truth = state['ground_truth']
    messages = state['messages']
    response = get_tutor_response.invoke({"history_chat":messages,"problem": problem, "ground_truth": ground_truth})
    messages.append({"role": "assistant", "content": response})
    state["messages"] = messages
    return state

def construct_agent():

    workflow = StateGraph(ChatState)

    workflow.add_node('dummy_node', identify_intent)
    workflow.add_node('tutor', tutor)
    workflow.add_node('solver', solver)
    workflow.add_node('call_general_chat', call_general_chat)
    workflow.add_node('web_search', web_searchh)

    workflow.add_conditional_edges(
        'dummy_node',
        which_tool,
        ['tutor','solver','call_general_chat', 'web_search']
    )

    workflow.add_edge(START,'dummy_node')
    workflow.add_edge('tutor',END) 
    workflow.add_edge('solver','dummy_node')
    workflow.add_edge('call_general_chat',END) 
    workflow.add_edge('web_search', END)

    from langgraph.checkpoint.memory import MemorySaver

    memory = MemorySaver()

    app = workflow.compile(checkpointer=memory)
    return app


