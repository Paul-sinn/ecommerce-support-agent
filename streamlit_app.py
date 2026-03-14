from uuid import uuid4

import streamlit as st
from dotenv import load_dotenv
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from graph.nodes.billing_agent import billing_agent
from graph.nodes.order_agent import order_agent
from graph.nodes.policy_completeness_guard import policy_completeness_guard
from graph.nodes.policy_risk_guard import policy_risk_guard
from graph.nodes.policy_scope_guard import policy_scope_guard
from graph.nodes.triage_router import triage_router
from graph.state import GraphState

load_dotenv()

PRODUCTS = [
    {"name": "Aurora Sneakers", "price": 129.0, "tag": "Best Seller"},
    {"name": "Metro Sling Bag", "price": 89.0, "tag": "New"},
    {"name": "Cloud Knit Hoodie", "price": 74.0, "tag": "Limited"},
    {"name": "Pulse Smart Watch", "price": 199.0, "tag": "Hot Deal"},
    {"name": "Luna Wireless Earbuds", "price": 159.0, "tag": "Popular"},
    {"name": "Nova Water Bottle", "price": 32.0, "tag": "Eco Pick"},
]


def route_to_agent(state: GraphState) -> str:
    if state.get("policy_status") in {"OUT_OF_SCOPE", "NEED_MORE_INFO"}:
        return "end"

    category = state.get("category")
    if category == "order":
        return "order_agent"
    if category == "billing":
        return "billing_agent"
    return "end"


@st.cache_resource
def build_app():
    graph = StateGraph(GraphState)
    graph.add_node("triage", triage_router)
    graph.add_node("policy_scope", policy_scope_guard)
    graph.add_node("policy_completeness", policy_completeness_guard)
    graph.add_node("policy_risk", policy_risk_guard)
    graph.add_node("order_agent", order_agent)
    graph.add_node("billing_agent", billing_agent)

    graph.set_entry_point("triage")
    graph.add_edge("triage", "policy_scope")
    graph.add_edge("policy_scope", "policy_completeness")
    graph.add_edge("policy_completeness", "policy_risk")
    graph.add_conditional_edges(
        "policy_risk",
        route_to_agent,
        {
            "order_agent": "order_agent",
            "billing_agent": "billing_agent",
            "end": END,
        },
    )
    graph.add_edge("order_agent", END)
    graph.add_edge("billing_agent", END)
    return graph.compile(checkpointer=MemorySaver())


def ensure_state():
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = f"thread-{uuid4()}"
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "cart" not in st.session_state:
        st.session_state.cart = []


def inject_styles():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&display=swap');
        .stApp {
            background: radial-gradient(circle at 20% 0%, #fdf2d0 0%, #fff6e5 30%, #eef7ff 100%);
            color: #1f2937;
            font-family: 'Space Grotesk', sans-serif;
        }
        .hero {
            background: linear-gradient(120deg, #0ea5a4 0%, #0f766e 45%, #0c4a6e 100%);
            padding: 24px;
            border-radius: 16px;
            color: white;
            margin-bottom: 16px;
        }
        .chip {
            display: inline-block;
            padding: 4px 10px;
            background: rgba(255,255,255,0.2);
            border-radius: 999px;
            margin-right: 6px;
            font-size: 12px;
        }
        .product-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 14px;
            padding: 14px;
            min-height: 160px;
            box-shadow: 0 8px 20px rgba(2, 6, 23, 0.06);
        }
        .tag {
            display: inline-block;
            background: #fef3c7;
            color: #92400e;
            border-radius: 999px;
            padding: 2px 8px;
            font-size: 11px;
            margin-bottom: 10px;
        }
        .chat-shell {
            background: #ffffffcc;
            border: 1px solid #dbeafe;
            border-radius: 16px;
            padding: 12px;
            box-shadow: 0 10px 20px rgba(30, 64, 175, 0.08);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def add_to_cart(index: int):
    st.session_state.cart.append(PRODUCTS[index])


def run_support_agent(app, prompt: str):
    config = {"configurable": {"thread_id": st.session_state.thread_id}}
    result = app.invoke({"messages": [{"role": "user", "content": prompt}]}, config=config)
    answer = result.get("final_reply") or result.get("policy_message")
    if not answer:
        category = result.get("category")
        if category in {"account", "technical"}:
            answer = f"Category '{category}' was recognized, but no dedicated agent is connected yet."
        elif category == "unknown":
            answer = "This request appears out of support scope."
        else:
            answer = "No response produced by the graph."
    return answer


st.set_page_config(page_title="NeoMall with Support Bot", page_icon="🛍️", layout="wide")
ensure_state()
inject_styles()
app = build_app()

left_col, right_col = st.columns([2.2, 1], gap="large")

with left_col:
    st.markdown(
        """
        <div class="hero">
            <h2 style="margin:0;">NeoMall Spring Drop</h2>
            <p style="margin:8px 0 12px 0;">Fake shopping mall for UX testing. Add items, ask support on the right.</p>
            <span class="chip">Fast Shipping</span>
            <span class="chip">7-Day Refund</span>
            <span class="chip">24/7 Support</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("Featured Products")
    row1 = st.columns(3)
    row2 = st.columns(3)
    grid = row1 + row2

    for i, product in enumerate(PRODUCTS):
        with grid[i]:
            st.markdown(
                f"""
                <div class="product-card">
                    <div class="tag">{product["tag"]}</div>
                    <h4 style="margin:0 0 8px 0;">{product["name"]}</h4>
                    <p style="margin:0 0 12px 0;color:#475569;">${product["price"]:.2f}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.button(
                "Add to Cart",
                key=f"add-{i}",
                use_container_width=True,
                on_click=add_to_cart,
                args=(i,),
            )

    st.subheader("Cart")
    if st.session_state.cart:
        total = 0.0
        for item in st.session_state.cart:
            total += item["price"]
            st.write(f"- {item['name']} (${item['price']:.2f})")
        st.success(f"Total: ${total:.2f}")
    else:
        st.info("Your cart is empty.")

with right_col:
    st.markdown('<div class="chat-shell">', unsafe_allow_html=True)
    st.subheader("Customer Support")
    st.caption("Order/Billing multi-turn test bot")
    st.code(st.session_state.thread_id)

    top_actions = st.columns(2)
    with top_actions[0]:
        if st.button("New Chat", use_container_width=True):
            st.session_state.thread_id = f"thread-{uuid4()}"
            st.session_state.chat_history = []
            st.rerun()
    with top_actions[1]:
        if st.button("Clear UI", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt = st.chat_input("배송/환불/결제 관련 질문을 입력하세요")
    if prompt:
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Analyzing..."):
                answer = run_support_agent(app, prompt)
                st.markdown(answer)
        st.session_state.chat_history.append({"role": "assistant", "content": answer})

    st.markdown("</div>", unsafe_allow_html=True)
