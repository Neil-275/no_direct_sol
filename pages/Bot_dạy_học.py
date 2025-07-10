import streamlit as st 
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

load_dotenv()

st.title("Bot dạy học")
math_solver_api = os.getenv('MATH_SOLVER')
math_tutor_api = os.getenv('MATH_TUTOR')

#define langgraph state
class ChatState(TypedDict):
    messages:List[Dict[str, Any]] = []
    ground_truth: str = ""
    problem: str = ""
    student_solution: str = ""
    student_get_it_right: int = 0

#define langgraph tool
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
    print("Extraction: ", response)
    result = json.loads(response.choices[0].message.content)
    # print("Extraction: ", result)
    if problem == "" and result["problem"] != "":
        state['problem'] = result['problem']
    if state['student_solution'] == "":
        state['student_solution'] = result['student_solution']
    if state['student_get_it_right'] == "":
        state['student_get_it_right'] = result['student_get_it_right']
    
    return state

def which_tool(state: ChatState): #conditional edge
    messages = state["messages"]
    problem = state['problem']
    ground_truth = state["ground_truth"]
    student_solution = state["student_solution"]
    student_get_it_right = state["student_get_it_right"]
    last_message = messages[-1]["content"]
    typee = ""
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


workflow = StateGraph(ChatState)


workflow.add_node('dummy_node', identify_intent)
workflow.add_node('tutor', tutor)
workflow.add_node('solver', solver)
workflow.add_node('call_general_chat', call_general_chat)

workflow.add_conditional_edges(
    'dummy_node',
    which_tool,
    ['tutor','solver','call_general_chat']
)

workflow.add_edge(START,'dummy_node')
workflow.add_edge('tutor',END) 
workflow.add_edge('solver','dummy_node')
workflow.add_edge('call_general_chat',END) 

from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()

app = workflow.compile(checkpointer=memory)
config = {'configurable': {"thread_id": "1"}}


import re

def convert_latex_to_markdown(text):
    # Pattern to match the entire LaTeX block
    pattern = r"\\\[(.*?)\\\]"
    
    # Function to replace each match with markdown LaTeX block
    def replacer(match):
        content = match.group(1).strip()
        return f"$$\n{content}\n$$"

    # Replace using re.sub with DOTALL to capture multiline LaTeX
    new_text = re.sub(pattern, replacer, text, flags=re.DOTALL)
    
    return new_text




### Streamlit session
if "messages" not in st.session_state:
    st.session_state["messages"] = [{'role':'assistant','content': 'Chào bạn, tôi là gia sư toán, có bằng tốt nghiệp xuất sắc sư phạm toán. Tôi có thể giúp gì được cho bạn'}]

if "problem" not in st.session_state:
    st.session_state["problem"] = ""

if "ground_truth" not in st.session_state:
    st.session_state["ground_truth"] = ""

if "student_solution" not in st.session_state:
    st.session_state["student_solution"] = ""

if "student_get_it_right" not in st.session_state:
    st.session_state["student_get_it_right"] = 0

# Render các message trước
for message in st.session_state["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Hỏi gì ?"):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        messages = [{"role": "system", "content": Tutor_prompt}]
        # messages = []
        messages += [{"role": m["role"], "content": m["content"]} for m in st.session_state["messages"]]
        # print(messages)
        
        # out = app.invoke({'messages': messages,
        #                 'problem': st.session_state['problem'],
        #                 'ground_truth': st.session_state['ground_truth']},
        #                 config)
        print("+++++++++++++++++ New iteration ++++++++++++++++++")
        for step in app.stream({'messages': messages,
                                'problem': st.session_state['problem'],
                                'ground_truth': st.session_state['ground_truth'],
                                'student_solution': st.session_state['student_solution'],
                                'student_get_it_right': st.session_state['student_get_it_right']},
                                config,
                                stream_mode='updates'):
            key = list(step.keys())[0]
            print("_________________\nStep output:")
            print("Node: ", list(step.keys())[0])
            print("messages:", step[key]['messages'][-1])
            for k in step[key].keys():
                if k != "messages":
                    print(f"{k}: {step[key][k]}")
            out = step
        last_state = None     
        if out.get("call_general_chat"):
            last_state = out["call_general_chat"]
        if out.get("tutor"):
            last_state = out["tutor"]
        if st.session_state['problem'] == "" and last_state['problem']:
            st.session_state['problem'] = last_state['problem']
        
        if st.session_state['ground_truth'] == "" and last_state['ground_truth']:
            st.session_state['ground_truth'] = last_state['ground_truth']
        full_response = convert_latex_to_markdown(last_state['messages'][-1]['content'])

        # for response in st.session_state['client'].chat.completions.create(
        #     model="gpt-3.5-turbo",
        #     messages=messages,
        #     stream=True):
        #     content = getattr(response.choices[0].delta, "content", "")
        #     full_response += content if type(content) == str else ""
        #     message_placeholder.markdown(full_response + "▌")

    message_placeholder.markdown(full_response)
    st.session_state["messages"].append({"role": "assistant", "content": full_response})    