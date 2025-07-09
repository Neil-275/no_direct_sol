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
    user_prompt = f"""
        Problem: {problem}
        Ground truth solution: {ground_truth}
        Dialogue_history: {history_chat}
    """

    payload = {"prompt": user_prompt, "language": "Tiếng Việt"}

    response = requests.post(math_tutor_api, json=payload)
    result = response.json()
    return result.get('response')

from langchain.chat_models import init_chat_model

model = init_chat_model("openai:gpt-4o-mini", temperature=0.4)

model = model.bind_tools([get_solver, get_tutor_response])

classify_client = openai.OpenAI()

def which_tool(state: ChatState): #edge
    messages = state["messages"]
    problem = state['problem']
    ground_truth = state["ground_truth"]
    student_solution = state["student_solution"]
    last_message = messages[-1]["content"]
    print("Messages: ",messages)
    response = classify_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": Classify_prompt(problem, student_solution, ground_truth, last_message)},
            ]
    )

    typee = response.choices[0].message.content
    print("type: ",typee)
    return typee.lower()

def call_general_model(state):
    messages = state["messages"]
    response = model.invoke(messages)
    messages.append({"role": "assistant", "content": response.content})
    return {"messages": messages}


def solver(state: ChatState):
    problem = state['problem']
    ground_truth = get_solver.invoke({"problem": problem})
    state.messages.append({"role": "assistant", "content": f"Here is the solution: {ground_truth}"})
    return {"messages": state.messages, "ground_truth": ground_truth}

def tutor(state: ChatState):
    problem = state['problem']
    ground_truth = state['ground_truth']
    messages = state['messages']
    response = get_tutor_response.invoke({"history_chat":messages,"problem": problem, "ground_truth": ground_truth})
    messages.append({"role": "assistant", "content": response})
    return {"messages": messages}

def dummy_node(state: ChatState):
  """A dummy node that does nothing."""
#   print("Dummy node triggered")
  return state

workflow = StateGraph(ChatState)


workflow.add_node('dummy_node', dummy_node)
workflow.add_node('tutor', tutor)
workflow.add_node('solver', solver)
workflow.add_node('call_general_chat', call_general_model)

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


### Streamlit session
if "messages" not in st.session_state:
    st.session_state["messages"] = [{'role':'assistant','content': 'Chào bạn, tôi có thể giúp gì được cho bạn'}]

if "problem" not in st.session_state:
    st.session_state["problem"] = []

if "ground_truth" not in st.session_state:
    st.session_state["ground_truth"] = []

if "student_solution" not in st.session_state:
    st.session_state["student_solution"] = []

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
        messages = []
        messages += [{"role": m["role"], "content": m["content"]} for m in st.session_state["messages"]]
        # print(messages)
        
        # out = app.invoke({'messages': messages,
        #                 'problem': st.session_state['problem'],
        #                 'ground_truth': st.session_state['ground_truth']},
        #                 config)
        
        for step in app.stream({'messages': messages,
                                'problem': st.session_state['problem'],
                                'ground_truth': st.session_state['ground_truth'],
                                'student_solution': st.session_state['student_solution']},
                                config,
                                stream_mode='updates'):
            print("Step output:", step)
            out = step     
        if out.get("call_general_chat"):
            full_response = out["call_general_chat"]['messages'][-1]['content']
        if out.get("tutor"):
            full_response = out["tutor"]['messages'][-1]['content']
        if st.session_state['problem'] == "" and out['problem']:
            st.session_state['problem'] = out['problem']
        
        if st.session_state['ground_truth'] == "" and out['ground_truth']:
            st.session_state['ground_truth'] = out['ground_truth']
        
        # for response in st.session_state['client'].chat.completions.create(
        #     model="gpt-3.5-turbo",
        #     messages=messages,
        #     stream=True):
        #     content = getattr(response.choices[0].delta, "content", "")
        #     full_response += content if type(content) == str else ""
        #     message_placeholder.markdown(full_response + "▌")

    message_placeholder.markdown(full_response)
    st.session_state["messages"].append({"role": "assistant", "content": full_response})    