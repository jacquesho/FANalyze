#!/usr/bin/env python3
"""
FANalyze Streamlit Chat Interface
Web UI for interacting with the FANalyze LangGraph agent with RAG capabilities.
"""

import time
import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langgraph.types import Command

# Add project root to path (go up one level from langgraph/)
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
load_dotenv(dotenv_path=project_root / ".env")

# Add langgraph directory to path so we can import agent module
# (avoiding conflict with installed langgraph package)
langgraph_dir = Path(__file__).parent
if str(langgraph_dir) not in sys.path:
    sys.path.insert(0, str(langgraph_dir))

# Import agent module (from langgraph/agent.py)
from agent import create_persistent_agent

# Import query helpers for formatting approval UI
try:
    from tools import (
        _generate_show_data_query,
        _generate_ticket_sales_query,
        analyze_query_complexity,
    )
except ImportError:
    # Fallback if direct import fails
    _generate_show_data_query = None
    _generate_ticket_sales_query = None
    analyze_query_complexity = None

# Page configuration
st.set_page_config(
    page_title="FANalyze AI Agent",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded",
)


def initialize_session_state():
    """Initialize Streamlit session state"""
    if "agent" not in st.session_state:
        with st.spinner("Initializing agent..."):
            try:
                st.session_state.agent = create_persistent_agent()
                st.success("✅ Agent initialized successfully!")
            except Exception as e:
                st.error(f"❌ Failed to initialize agent: {e}")
                st.info("💡 Make sure PostgreSQL is running and LangGraph database is set up.")
                st.info("💡 Run: python langgraph/scripts/create_langgraph_service_user.py")
                st.session_state.agent = None

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "thread_id" not in st.session_state:
        st.session_state.thread_id = f"fanalyze_thread_{int(time.time())}"

    if "user_name" not in st.session_state:
        st.session_state.user_name = "User"

    if "session_id" not in st.session_state:
        st.session_state.session_id = f"fanalyze_session_{int(time.time())}"

    if "conversation_metadata" not in st.session_state:
        st.session_state.conversation_metadata = {
            st.session_state.thread_id: {
                "name": "Main Conversation",
                "created_at": time.time(),
                "message_count": 0,
                "user_name": st.session_state.user_name,
            }
        }
    
    if "pending_query_approval" not in st.session_state:
        st.session_state.pending_query_approval = None
    
    if "graph_image" not in st.session_state:
        st.session_state.graph_image = None
    
    if "graph_question" not in st.session_state:
        st.session_state.graph_question = None
    
    if "current_question" not in st.session_state:
        st.session_state.current_question = None


def create_new_thread():
    """Create a new conversation thread"""
    new_thread_id = f"thread_{int(time.time())}"
    st.session_state.thread_id = new_thread_id
    st.session_state.messages = []

    # Add to conversation metadata
    st.session_state.conversation_metadata[new_thread_id] = {
        "name": f"Conversation {len(st.session_state.conversation_metadata)}",
        "created_at": time.time(),
        "message_count": 0,
        "user_name": st.session_state.user_name,
    }
    st.rerun()


def display_conversation_history():
    """Display the conversation history"""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


def get_agent_response(user_input: str):
    """Get response from the agent using PostgreSQL persistence"""
    if st.session_state.agent is None:
        return "❌ Agent not initialized. Please check the error message above."

    try:
        # Create configuration for this thread
        config = {"configurable": {"thread_id": st.session_state.thread_id}}

        # Get current conversation metadata
        current_metadata = st.session_state.conversation_metadata.get(
            st.session_state.thread_id, {}
        )

        # Prepare initial state
        initial_state = {
            "messages": [HumanMessage(content=user_input)],
            "user_name": st.session_state.user_name,
            "conversation_count": current_metadata.get("message_count", 0),
            "session_id": st.session_state.session_id,
            "thread_metadata": {
                "created_at": current_metadata.get("created_at", time.time()),
                "user_name": st.session_state.user_name,
                "thread_name": current_metadata.get("name", "Unknown"),
                "interface": "streamlit",
            },
        }

        # Get agent response - handle interrupts for query approval
        result = st.session_state.agent.invoke(initial_state, config)
        
        # Check for interrupt (expensive query needs approval)
        if "__interrupt__" in result:
            # Get the current state to extract query details
            current_state = st.session_state.agent.get_state(config)
            state_value = current_state.values if hasattr(current_state, 'values') else {}
            
            # Extract query info from the last message (tool_call)
            query_details = None
            if state_value.get("messages"):
                last_msg = state_value["messages"][-1]
                if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                    # We'll need to regenerate the query info
                    # For now, store what we can
                    query_details = {
                        "tool_calls": last_msg.tool_calls,
                        "interrupt_value": result["__interrupt__"],
                    }
            
            # Store interrupt info for UI display
            st.session_state.pending_query_approval = {
                "interrupt_value": result["__interrupt__"],
                "config": config,
                "query_details": query_details,
                "state": state_value,
            }
            # Return special marker to trigger UI
            return "__QUERY_APPROVAL_NEEDED__"
        
        # Normal response
        response = result["messages"][-1].content

        # Update conversation metadata
        if st.session_state.thread_id in st.session_state.conversation_metadata:
            st.session_state.conversation_metadata[st.session_state.thread_id][
                "message_count"
            ] += 1

        return response
    except Exception as e:
        return f"❌ Error: {e}"


def main():
    """Main Streamlit application"""

    # Initialize session state
    initialize_session_state()

    # Header
    st.title("🎵 FANalyze AI Agent")
    st.markdown("**Concert Analytics & Document Search with RAG**")

    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")

        # User name input
        user_name = st.text_input(
            "Your Name",
            value=st.session_state.user_name,
            help="Enter your name for personalized conversations",
        )
        if user_name != st.session_state.user_name:
            st.session_state.user_name = user_name
            st.rerun()

        st.divider()

        # Thread management
        st.header("🧵 Thread Management")

        # Current thread display
        st.write("**Current Thread:**")
        st.code(st.session_state.thread_id)

        # New thread button
        if st.button("🆕 New Conversation", use_container_width=True):
            create_new_thread()

        # Thread ID input
        new_thread_id = st.text_input(
            "Switch to Thread ID",
            placeholder="Enter thread ID to switch",
            help="Enter a thread ID to continue a previous conversation",
        )

        if st.button("🔄 Switch Thread", use_container_width=True) and new_thread_id:
            st.session_state.thread_id = new_thread_id
            st.session_state.messages = []

            # Add to metadata if not exists
            if new_thread_id not in st.session_state.conversation_metadata:
                st.session_state.conversation_metadata[new_thread_id] = {
                    "name": f"Conversation {len(st.session_state.conversation_metadata)}",
                    "created_at": time.time(),
                    "message_count": 0,
                    "user_name": st.session_state.user_name,
                }
            st.rerun()

        # Show current thread info
        st.write(f"**Current Thread:** {st.session_state.thread_id}")

        # Always show available conversations
        st.write("**Available Conversations:**")
        for thread_id, metadata in st.session_state.conversation_metadata.items():
            status = "🟢" if thread_id == st.session_state.thread_id else "⚪"
            st.write(
                f"{status} {thread_id}: {metadata['name']} ({metadata['message_count']} messages)"
            )

        st.divider()

        # Session info
        st.header("📊 Session Info")
        st.write(f"**Session ID:** {st.session_state.session_id}")
        st.write(f"**Messages:** {len(st.session_state.messages)}")
        st.write(f"**User:** {st.session_state.user_name}")

        # Current conversation info
        current_metadata = st.session_state.conversation_metadata.get(
            st.session_state.thread_id, {}
        )
        st.write(f"**Thread Messages:** {current_metadata.get('message_count', 0)}")
        st.write(
            f"**Thread Created:** {time.ctime(current_metadata.get('created_at', time.time()))}"
        )

        st.divider()

        # Agent info
        st.header("🤖 Agent Info")
        st.write("**Model:** GPT-3.5 Turbo")
        st.write("**Framework:** LangGraph")
        st.write("**Storage:** PostgreSQL")

        # Available tools
        st.header("🛠️ Available Tools")
        st.write("• **query_show_data**: Query concerts and shows")
        st.write("• **query_ticket_sales**: Query ticket sales data")
        st.write("• **search_documents**: Search documents (RAG)")

        # Persistent storage info
        st.header("💾 Persistent Storage")
        st.write("**Database:** PostgreSQL")
        st.write("**Status:** ✅ Connected" if st.session_state.agent else "❌ Not Connected")
        st.write("**Features:**")
        st.write("• Conversation persistence")
        st.write("• Thread isolation")
        st.write("• Cross-session memory")

        # Example queries
        st.divider()
        st.header("💡 Example Queries")
        example_queries = [
            "What shows are coming up?",
            "Show me recent ticket sales",
            "What are the ticket sales strategies?",
            "Tell me about Metallica's history",
        ]
        for query in example_queries:
            if st.button(f"💬 {query}", key=f"example_{query}", use_container_width=True):
                # Simulate user input
                if prompt := st.chat_input("Type your message here..."):
                    pass  # This will be handled by the chat input below

        # Clear conversation button
        if st.button("🗑️ Clear Conversation", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
        
        st.divider()
        
        # Graph visualization
        st.header("📊 Graph Visualization")
        st.write("View the LangGraph workflow structure")
        
        if st.button("🔄 Generate Graph", use_container_width=True):
            if st.session_state.agent:
                try:
                    with st.spinner("Generating graph visualization..."):
                        graph_png = st.session_state.agent.get_graph().draw_mermaid_png()
                        st.session_state.graph_image = graph_png
                        # Store the current question or last user question if available
                        if st.session_state.current_question:
                            st.session_state.graph_question = st.session_state.current_question
                        elif st.session_state.messages:
                            last_user_msg = next(
                                (msg for msg in reversed(st.session_state.messages) if msg["role"] == "user"),
                                None
                            )
                            st.session_state.graph_question = last_user_msg["content"] if last_user_msg else "Graph generated"
                        else:
                            st.session_state.graph_question = "Graph generated"
                        st.success("✅ Graph generated!")
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ Failed to generate graph: {e}")
            else:
                st.warning("⚠️ Agent not initialized")
        
        # Display stored graph if available
        if st.session_state.graph_image:
            st.write("**Generated for:**")
            st.info(st.session_state.graph_question)
            st.image(st.session_state.graph_image, use_container_width=True)
            
            # Download button
            st.download_button(
                label="📥 Download Graph",
                data=st.session_state.graph_image,
                file_name=f"fanalyze_graph_{int(time.time())}.png",
                mime="image/png",
                use_container_width=True
            )

    # Main chat interface
    st.header("💬 Chat")

    # Display conversation history
    display_conversation_history()

    # Check for pending query approval - show inline after user's last message
    if st.session_state.pending_query_approval:
        pending = st.session_state.pending_query_approval
        # Extract query info from state
        query_info = None
        if pending.get("state") and pending["state"].get("messages"):
            messages = pending["state"]["messages"]
            for msg in reversed(messages):
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    # Regenerate query for display
                    if not all([_generate_show_data_query, _generate_ticket_sales_query, analyze_query_complexity]):
                        query_info = None
                        break
                    
                    tool_call = msg.tool_calls[0]
                    tool_name = tool_call["name"]
                    args = tool_call["args"]
                    
                    if tool_name == "query_show_data":
                        query = _generate_show_data_query(
                            artist_name=args.get("artist_name"),
                            show_type=args.get("show_type", "all"),
                            limit=args.get("limit", 50)
                        )
                    elif tool_name == "query_ticket_sales":
                        query = _generate_ticket_sales_query(
                            artist_name=args.get("artist_name"),
                            venue_name=args.get("venue_name"),
                            hours=args.get("hours", 24),
                            limit=args.get("limit", 50)
                        )
                    else:
                        query = None
                    
                    if query:
                        analysis = analyze_query_complexity(query)
                        query_info = {
                            "query": query,
                            "tool_name": tool_name,
                            "reasons": analysis["reasons"],
                            "estimated_cost": analysis["estimated_cost"].upper(),
                        }
                    break
        
        # Show approval UI as an assistant message (inline with conversation)
        with st.chat_message("assistant"):
            st.warning("⚠️ **Expensive Query Detected - Approval Required**")
            with st.expander("📋 View Query Details", expanded=True):
                if query_info:
                    st.markdown("**SQL Query:**")
                    st.code(query_info["query"], language="sql")
                    st.markdown("\n**Concerns:**")
                    for reason in query_info["reasons"]:
                        st.markdown(f"  • {reason}")
                    st.markdown(f"\n**Estimated Cost:** {query_info['estimated_cost']}")
                else:
                    # Fallback to interrupt message if we can't extract query
                    st.markdown(pending["interrupt_value"])
            
            col1, col2 = st.columns(2)
            approval_decision = None
            
            with col1:
                if st.button("✅ Approve Query", use_container_width=True, type="primary", key="approve_query"):
                    approval_decision = "yes"
            
            with col2:
                if st.button("❌ Cancel Query", use_container_width=True, key="cancel_query"):
                    approval_decision = "no"
            
            if approval_decision:
                # Resume agent with user's decision
                config = pending["config"]
                with st.spinner("Processing..."):
                    result = st.session_state.agent.invoke(
                        Command(resume=approval_decision), 
                        config
                    )
                    # Get response
                    if result.get("messages"):
                        final_response = result["messages"][-1].content
                    else:
                        final_response = "Query executed successfully." if approval_decision == "yes" else "Query cancelled."
                    
                    # Add response to messages
                    st.session_state.messages.append({"role": "assistant", "content": final_response})
                    st.session_state.pending_query_approval = None
                    st.rerun()

    # Chat input - disable if there's a pending approval
    chat_disabled = st.session_state.pending_query_approval is not None
    if prompt := st.chat_input("Type your message here...", disabled=chat_disabled):
        # Don't process new messages if there's a pending approval
        if st.session_state.pending_query_approval:
            st.warning("⚠️ Please approve or cancel the pending query before sending a new message.")
            st.stop()
        
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Store the question for potential graph generation
        st.session_state.current_question = prompt

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get and display agent response
        with st.chat_message("assistant"):
            with st.spinner("Agent is thinking..."):
                response = get_agent_response(prompt)
                
                # Check if query approval is needed
                if response == "__QUERY_APPROVAL_NEEDED__":
                    # Approval UI will be shown inline - trigger rerun to display it
                    st.info("⏳ Query requires approval. Please review the approval prompt below.")
                    # Rerun immediately to show the approval UI
                    st.rerun()
                else:
                    # Normal response
                    st.markdown(response)
                    # Add agent response to chat history
                    st.session_state.messages.append({"role": "assistant", "content": response})

    # Footer
    st.divider()
    st.markdown(
        """
        <div style='text-align: center; color: #666;'>
            <p>🎵 FANalyze AI Agent powered by LangGraph | RAG with Pinecone | Foundry AI Academy</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()

