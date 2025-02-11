import streamlit as st
import logging
from typing import Dict, Any, Optional
from omniguard import omniguard_check, process_omniguard_result, fetch_assistant_response

def process_user_message(
    user_input: str,
    session_state: Dict[str, Any],
    generate_conversation_id,
    update_conversation_context
) -> None:
    """
    Process a user message, update conversation state, and handle OmniGuard checks.
    
    Args:
        user_input: The user's input message
        session_state: Streamlit session state containing conversation data
        generate_conversation_id: Function to generate new conversation IDs
        update_conversation_context: Function to update the conversation context
    """
    if not user_input or not isinstance(user_input, str):
        return  # Skip processing empty or non-string messages
    
    user_input = user_input.strip()
    session_state["turn_number"] += 1
    session_state["conversation_id"] = generate_conversation_id(session_state["turn_number"])
    session_state["messages"].append({"role": "user", "content": user_input})
    update_conversation_context()  # Refresh context after adding the new message

    with st.chat_message("user"):
        st.markdown(user_input)

    handle_raw_response(user_input, session_state)
    handle_omniguard_check(user_input, session_state)

def handle_raw_response(user_input: str, session_state: Dict[str, Any]) -> None:
    """
    Handle fetching raw assistant response if enabled.
    
    Args:
        user_input: The user's input message
        session_state: Streamlit session state containing conversation data
    """
    if session_state["show_unfiltered_response"]:
        try:
            with st.spinner("Fetching raw response..."):
                session_state["raw_assistant_response"] = fetch_assistant_response(
                    user_input,
                    skip_omniguard=True
                )
        except Exception as ex:
            st.error(f"Error fetching raw response: {ex}")
            logging.exception("Exception occurred during raw response fetch")
            session_state["raw_assistant_response"] = "Error: Could not fetch raw response"

def handle_omniguard_check(user_input: str, session_state: Dict[str, Any]) -> None:
    """
    Handle OmniGuard safety check for user input.
    
    Args:
        user_input: The user's input message
        session_state: Streamlit session state containing conversation data
    """
    try:
        with st.spinner("OmniGuard..."):
            omniguard_response = omniguard_check()
    except Exception as ex:
        st.error(f"Error calling OmniGuard: {ex}")
        logging.exception("Exception occurred during OmniGuard call")
        omniguard_response = {
            "response": {
                "action": "UserInputRejection",
                "UserInputRejection": "Safety system unavailable - please try again"
            }
        }

    last_msg = session_state["messages"][-1] if session_state["messages"] else {}
    context = f"{last_msg['role']}: {last_msg['content']}" if last_msg else ""
    process_omniguard_result(omniguard_response, user_input, context)

def get_user_input() -> Optional[str]:
    """Get user input from the chat input field."""
    return st.chat_input("Type your message here", max_chars=20000, key="chat_input")