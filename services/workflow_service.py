import asyncio
from typing import Dict, List, Any, Optional
from models.request_response_models import WorkflowStep, WorkflowState
from services.agents_service import run_agent_with_context
import utilities.pg_sql_db_util as db_util


class WorkflowManager:
    def __init__(self):
        # In-memory workflows for running workflows
        self.workflows: Dict[str, WorkflowState] = {}

    def create_workflow(self, workflow_id: str, steps: List[WorkflowStep], user_id: Optional[int] = None, 
                        name: str = "Untitled Workflow", description: str = None, is_drafted: bool = False):
        """Create a new workflow with steps or update an existing one."""
        
        # Check if workflow already exists in memory
        existing_workflow = self.get_workflow(workflow_id)
        
        if existing_workflow:
            # Update existing workflow
            existing_workflow.steps = steps
            existing_workflow.current_index = 0  # Reset for draft
            existing_workflow.outputs = []  # Clear outputs for draft
            existing_workflow.context = {}  # Reset context
            existing_workflow.is_drafted = is_drafted
            self.workflows[workflow_id] = existing_workflow
        else:
            # Create new workflow
            self.workflows[workflow_id] = WorkflowState(steps)
            self.workflows[workflow_id].is_drafted = is_drafted
        
        # Initialize context
        workflow = self.workflows[workflow_id]
        for i, step in enumerate(steps):
            if step.metadata:
                step_prefix = f"step_{i+1}_metadata_"
                for key, value in step.metadata.items():
                    context_key = f"{step_prefix}{key}"
                    workflow.context[context_key] = value
        
        # If user_id is provided, store in database
        if user_id:
            with db_util.SessionLocal() as db:
                db_util.create_workflow(db, workflow_id, user_id, steps, name, description, is_drafted)
        
        return self.workflows[workflow_id]
        


    def get_workflow(self, workflow_id: str) -> Optional[WorkflowState]:
        """Get workflow by ID, first looking in memory then in database."""
        # First check in-memory workflows
        if workflow_id in self.workflows:
            return self.workflows[workflow_id]
        
        # If not in memory, check database
        with db_util.SessionLocal() as db:
            db_workflow = db_util.get_workflow(db, workflow_id)
            if db_workflow:
                # Convert DB workflow to WorkflowState
                workflow_state = db_util.workflow_to_workflow_state(db_workflow)
                # Add event for async operations
                workflow_state.event = asyncio.Event()
                # Store in memory for future use
                self.workflows[workflow_id] = workflow_state
                return workflow_state
        
        return None
    
    def update_context(self, workflow_id: str, key: str, value: Any):
        """Update the shared context for a workflow."""
        if workflow_id in self.workflows:
            self.workflows[workflow_id].context[key] = value
            
            # Update in database if it exists
            with db_util.SessionLocal() as db:
                db_workflow = db_util.get_workflow(db, workflow_id)
                if db_workflow:
                    db_util.update_workflow_context(db, workflow_id, key, str(value))
            
            return True
        return False
    
    def get_context(self, workflow_id: str) -> Dict[str, Any]:
        """Get the shared context for a workflow."""
        if workflow_id in self.workflows:
            return self.workflows[workflow_id].context
        
        # If not in memory, check database
        with db_util.SessionLocal() as db:
            return db_util.get_workflow_context(db, workflow_id)
        
        return {}
    
    def add_output(self, workflow_id: str, agent_name: str, output: Any):
        """Add an output to the workflow results."""

        # print("in workflow add_output")
        # print(workflow_id)
        # print(self.workflows)

        if workflow_id in self.workflows:
            self.workflows[workflow_id].outputs.append({
                "agent": agent_name,
                "output": output,
                "edited": False  # Track if this output was edited
            })
            # Automatically add this output to the context for future steps
            output_key = f"output_from_{agent_name}"
            self.update_context(workflow_id, output_key, output)
            
            # Add to database if it exists
            with db_util.SessionLocal() as db:
                db_workflow = db_util.get_workflow(db, workflow_id)
                print(db_workflow.workflow_id)
                if db_workflow:
                    db_util.add_workflow_output(db, workflow_id, agent_name, str(output))
            
            return True
        return False
    
    def set_feedback(self, workflow_id: str, feedback: str):
        """Set feedback for a workflow."""
        if workflow_id in self.workflows:
            self.workflows[workflow_id].feedback = feedback
            
            # Update in database if it exists
            with db_util.SessionLocal() as db:
                db_workflow = db_util.get_workflow(db, workflow_id)
                if db_workflow:
                    db_util.update_workflow_approval(db, workflow_id, False, feedback)
            
            return True
        return False
    
    def set_edited_output(self, workflow_id: str, edited_output: str) -> bool:
        """Set user-edited output for the current step."""
        if workflow_id in self.workflows:
            workflow = self.workflows[workflow_id]
            workflow.edited_output = edited_output
            
            # Update the most recent output with the edited content
            if workflow.outputs:
                workflow.outputs[-1]["output"] = edited_output
                workflow.outputs[-1]["edited"] = True
                
                # Update the context with the edited output
                agent_name = workflow.outputs[-1]["agent"]
                output_key = f"output_from_{agent_name}"
                self.update_context(workflow_id, output_key, edited_output)
                
                # Update in database if it exists
                with db_util.SessionLocal() as db:
                    db_workflow = db_util.get_workflow(db, workflow_id)
                    if db_workflow and db_workflow.outputs:
                        step_order = len(db_workflow.outputs) - 1
                        db_util.update_workflow_output(db, workflow_id, step_order, edited_output, True)
            
            return True
        return False
    
    def next_step(self, workflow_id: str) -> bool:
        """Move to the next step in the workflow."""
        if workflow_id in self.workflows:
            workflow = self.workflows[workflow_id]
            if workflow.current_index < len(workflow.steps) - 1:
                workflow.current_index += 1
                
                # Update in database if it exists
                with db_util.SessionLocal() as db:
                    db_workflow = db_util.get_workflow(db, workflow_id)
                    if db_workflow:
                        is_completed = workflow.current_index >= len(workflow.steps)
                        db_util.update_workflow_status(db, workflow_id, workflow.current_index, is_completed)
                
                return True
        return False
    
    def current_step(self, workflow_id: str) -> Optional[WorkflowStep]:
        """Get the current step for a workflow."""
        if workflow_id in self.workflows:
            workflow = self.workflows[workflow_id]
            if 0 <= workflow.current_index < len(workflow.steps):
                return workflow.steps[workflow.current_index]
        return None
    
    def update_workflow_status(self, workflow_id: str, is_completed: bool = False):
        """Update the workflow status in the database."""
        workflow = self.get_workflow(workflow_id)
        if workflow:
            with db_util.SessionLocal() as db:
                db_util.update_workflow_status(db, workflow_id, workflow.current_index, is_completed)
            return True
        return False
    


async def execute_workflow(manager: WorkflowManager, workflow_id: str, user_id: int):
    """Execute workflow using individual agents sequentially with context passing"""
    workflow = manager.get_workflow(workflow_id)
    if not workflow:
        print(f"Workflow {workflow_id} not found")
        return
    
    while workflow.current_index < len(workflow.steps):
        current_step = workflow.steps[workflow.current_index]
        agent_name = current_step.name
        prompt = current_step.prompt
        
        # Get context from previous steps
        context = manager.get_context(workflow_id)
        
        if current_step.metadata:
            context["current_step_metadata"] = current_step.metadata
        
        try:
            print(f"Running agent: {agent_name} (Step {workflow.current_index + 1}/{len(workflow.steps)})")
            
            # Run the agent and get response
            response = await run_agent_with_context(agent_name, prompt, context, workflow_id, user_id)
            output_content = response.content if hasattr(response, 'content') else str(response)
            # print(output_content)
            
            # Store the output in both memory AND database
            with db_util.SessionLocal() as db:
                # Add to workflow outputs
                manager.add_output(workflow_id, agent_name, output_content)
                
                # Explicitly update database status
                db_util.update_workflow_status(
                    db, 
                    workflow_id, 
                    workflow.current_index,
                    workflow.current_index >= len(workflow.steps) - 1
                )
            
            # Handle human review if required
            if current_step.human_review:
                while True:
                    print(f"Waiting for human review for agent: {agent_name}")
                    await workflow.event.wait()
                    
                    if workflow.approved:
                        workflow.event.clear()
                        workflow.approved = None
                        break
                    else:
                        # Regenerate with feedback
                        feedback = workflow.feedback
                        new_prompt = f"{prompt}\n\n## Feedback from review:\n{feedback}"
                        
                        # Re-run with feedback
                        response = await run_agent_with_context(agent_name, new_prompt, context, workflow_id, user_id)
                        output_content = response.content if hasattr(response, 'content') else str(response)
                        
                        # Update output in both memory AND database
                        with db_util.SessionLocal() as db:
                            workflow.outputs[-1]["output"] = output_content
                            workflow.outputs[-1]["edited"] = False
                            manager.update_context(workflow_id, f"output_from_{agent_name}", output_content)
                            
                            # Update the specific output in database
                            step_order = len(workflow.outputs) - 1
                            db_util.update_workflow_output(
                                db, 
                                workflow_id, 
                                step_order, 
                                output_content, 
                                False
                            )
                            
                            # Reset approval state
                            db_util.clear_workflow_approval(db, workflow_id)
                        
                        workflow.event.clear()
                        workflow.approved = None
            
            # Move to next step
            workflow.current_index += 1
            
        except Exception as e:
            print(f"Error executing step {workflow.current_index}: {str(e)}")
            
            # Ensure error is stored in both memory AND database
            with db_util.SessionLocal() as db:
                manager.add_output(workflow_id, agent_name, f"Error: {str(e)}")
                db_util.update_workflow_status(
                    db, 
                    workflow_id, 
                    workflow.current_index,
                    workflow.current_index >= len(workflow.steps) - 1
                )
            
            workflow.current_index += 1