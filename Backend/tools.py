import json
from database import (
    create_interview,
    get_all_interviews,
    get_interview_by_id,
    update_interview,
    delete_interview
)
 
# These are the tools that the AI agent can "decide to use"
# Each tool is a function that the LLM can call
 
def tool_create_interview(title: str, description: str = "", scheduled_date: str = None) -> str:
    """
    Tool: Create a new interview.
    The AI agent calls this when a user wants to schedule an interview.
   
    Args:
        title: Interview title (e.g., "Python Developer - Alice")
        description: Interview details
        scheduled_date: optional scheduled date string
   
    Returns:
        JSON string with the created interview
    """
    try:
        interview = create_interview(title, description, scheduled_date)
        return json.dumps({
            "status": "success",
            "message": f"✓ Interview created: {title}",
            "interview": interview
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Error creating interview: {str(e)}"
        })
 
def tool_read_interviews() -> str:
    """
    Tool: Read all interviews.
    The AI agent calls this when a user wants to see all interviews.
   
    Returns:
        JSON string with list of interviews
    """
    try:
        interviews = get_all_interviews()
        return json.dumps({
            "status": "success",
            "interviews": interviews,
            "count": len(interviews)
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Error reading interviews: {str(e)}"
        })
 
def tool_update_interview(interview_id: int, title: str = None, description: str = None, scheduled_date: str = None) -> str:
    """
    Tool: Update an existing interview.
    The AI agent calls this when a user wants to modify an interview.
   
    Args:
        interview_id: ID of the interview to update
        title: New title (optional)
        description: New description (optional)
        scheduled_date: New scheduled date (optional)
   
    Returns:
        JSON string with success/error message
    """
    try:
        update_interview(interview_id, title, description, scheduled_date)
        interviews = get_all_interviews()
        return json.dumps({
            "status": "success",
            "message": f"✓ Interview {interview_id} updated",
            "interviews": interviews
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Error updating interview: {str(e)}"
        })
 
def tool_delete_interview(interview_id: int) -> str:
    """
    Tool: Delete an interview.
    The AI agent calls this when a user wants to cancel an interview.
   
    Args:
        interview_id: ID of the interview to delete
   
    Returns:
        JSON string with success/error message
    """
    try:
        delete_interview(interview_id)
        interviews = get_all_interviews()
        return json.dumps({
            "status": "success",
            "message": f"✓ Interview {interview_id} deleted",
            "interviews": interviews
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Error deleting interview: {str(e)}"
        })


def tool_read_interview(interview_id: int) -> str:
    """
    Tool: Read a single interview by id.
    """
    try:
        interview = get_interview_by_id(interview_id)
        if interview is None:
            return json.dumps({"status": "error", "message": "Interview not found", "interview": None})
        return json.dumps({"status": "success", "interview": interview})
    except Exception as e:
        return json.dumps({"status": "error", "message": f"Error reading interview: {str(e)}"})
 
# Dictionary of available tools
# The AI agent will use this to decide which tool to call
TOOLS = {
    "create_interview": tool_create_interview,
    "read_interviews": tool_read_interviews,
    "read_interview": tool_read_interview,
    "update_interview": tool_update_interview,
    "delete_interview": tool_delete_interview
}
 