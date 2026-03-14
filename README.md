# ecommerce-support-agent
A multi-agent AI customer support system for e-commerce with policy guardrails, intent routing, and workflow-based agent orchestration.

Ecommerce Support Agent

A multi-agent AI customer support system for e-commerce that filters requests through policy guardrails and routes them to specialized agents using a workflow-based architecture.

This project demonstrates how customer inquiries can be processed through a structured pipeline that enforces store policies, evaluates request scope and risk, and routes the request to the appropriate support agent.

Architecture

The system processes user requests through multiple stages before delegating them to specialized agents.

Workflow overview:

Triage
The system analyzes the user's message and determines the initial category of the request.

Policy Scope Check
Ensures the request falls within the store's supported policies.

Policy Completeness Validation
Verifies that the user has provided sufficient information to proceed.

Policy Risk Evaluation
Detects potentially risky or restricted requests.

Agent Routing
Based on the evaluation, the request is routed to the appropriate agent:

Billing Agent – handles payment, refund, and billing inquiries

Order Agent – handles order status, shipping, and purchase-related requests

If a request fails policy validation or is outside scope, the workflow terminates early.

System Flow

User Message
     ↓
Triage
     ↓
Policy Scope Check
     ↓
Policy Completeness
     ↓
Policy Risk Evaluation
     ↓
Routing
   ↙        ↘
Billing     Order
 Agent      Agent
     ↓
   Response




Features

Multi-agent architecture

Policy guardrails for safe request handling

Workflow-based request routing

Specialized agents for different support tasks

Modular design for easy extension

Example Use Cases

Customer messages like:

“Where is my order?”

“I want a refund”

“My payment failed”

The system:

analyzes the request

checks store policies

evaluates risk

routes the request to the correct support agent

Tech Stack

Python

Multi-agent workflow architecture

Policy guardrails

Agent routing system

(Optional depending on your implementation)

LangGraph

LLM APIs

FastAPI / Flask

Future Improvements

Product recommendation agent

Return & exchange agent

Knowledge base integration

Conversation memory

Full ecommerce backend integration

Purpose

This project demonstrates how AI agent workflows can be applied to real-world customer support automation in e-commerce systems.
