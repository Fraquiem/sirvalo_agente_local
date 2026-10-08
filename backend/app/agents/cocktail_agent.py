from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END

class AgentState(TypedDict):
    question: str
    user_id: str
    documents: List[Dict[str, Any]]
    is_context_sufficient: bool
    response: str
    sources: List[str]
    error: Optional[str]

def retrieve_context(state: AgentState) -> AgentState:
    """Nodo 2: Recuperar documentos relevantes desde la base vectorial de Supabase."""
    # TODO: Implementar consulta a vectorstore
    return state

def validate_relevance(state: AgentState) -> AgentState:
    """Nodo 3: Evaluar si el contexto recuperado es suficiente para responder la pregunta."""
    # TODO: Implementar lógica de suficiencia (umbral o LLM evaluation)
    return state

def generate_response(state: AgentState) -> AgentState:
    """Nodo 4: Generar la respuesta combinando el contexto con el LLM local (Ollama)."""
    # TODO: Implementar generación de respuesta restrictiva
    return state

def reject_question(state: AgentState) -> AgentState:
    """Nodo 5: Responder con rechazo explícito si la información es insuficiente."""
    state["response"] = "No tengo suficiente información en mi base de conocimiento para responder esa pregunta."
    return state

def save_interaction(state: AgentState) -> AgentState:
    """Nodo 6: Guardar la conversación y el mensaje resultante en la base de datos."""
    # TODO: Implementar guardado en historial de conversaciones
    return state

# Lógica para construir el grafo
def build_agent_graph():
    workflow = StateGraph(AgentState)
    
    # 1. Definición de nodos
    workflow.add_node("retrieve", retrieve_context)
    workflow.add_node("validate", validate_relevance)
    workflow.add_node("generate", generate_response)
    workflow.add_node("reject", reject_question)
    workflow.add_node("save", save_interaction)
    
    # 2. Configurar el flujo
    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "validate")
    
    # Decisión condicional según la suficiencia del contexto
    workflow.add_conditional_edges(
        "validate",
        lambda state: "generate" if state.get("is_context_sufficient") else "reject",
        {
            "generate": "generate",
            "reject": "reject"
        }
    )
    
    workflow.add_edge("generate", "save")
    workflow.add_edge("reject", "save")
    workflow.add_edge("save", END)
    
    return workflow.compile()
