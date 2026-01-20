import streamlit as st
import requests
import pandas as pd
from datetime import datetime

API_BASE = "http://localhost:8001/api/"

st.title("TaskTracker - Enterprise Task Management")

def test_api_connection():
    try:
        response = requests.get(f"{API_BASE}tasks/", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        st.error(f"API Connection failed: {e}")
        return False

menu = st.sidebar.selectbox("Menu", ["Dashboard", "Projects", "Tasks", "Users"])

if test_api_connection():
    st.sidebar.success("API Connected")
else:
    st.sidebar.error("API Not Connected")

if menu == "Dashboard":
    st.header("Dashboard")
    try:
        projects_response = requests.get(f"{API_BASE}projects/", timeout=10)
        tasks_response = requests.get(f"{API_BASE}tasks/", timeout=10)
        
        if projects_response.status_code == 200 and tasks_response.status_code == 200:
            projects = projects_response.json()
            tasks = tasks_response.json()
            st.metric("Total Projects", len(projects))
            st.metric("Total Tasks", len(tasks))
            if tasks:
                statuses = [task.get('status', '') for task in tasks if task.get('status')]
                if statuses:
                    status_counts = pd.Series(statuses).value_counts()
                    st.bar_chart(status_counts)
                else:
                    st.write("No task statuses available.")
            else:
                st.write("No tasks to display.")
        else:
            st.error(f"API Error: Projects {projects_response.status_code}, Tasks {tasks_response.status_code}")
    except requests.exceptions.RequestException as e:
        st.error(f"Unable to connect to API: {e}")

elif menu == "Projects":
    st.header("Projects")
    with st.expander("Add New Project"):
        with st.form("new_project_form"):
            project_name = st.text_input("Project Name")
            project_description = st.text_area("Description")
            submitted = st.form_submit_button("Create Project")
            if submitted:
                if project_name:
                    data = {
                        "name": project_name,
                        "description": project_description,
                        "owner": 1,  
                        "members": [] 
                    }
                    try:
                        response = requests.post(f"{API_BASE}projects/", json=data, timeout=10)
                        if response.status_code == 201:
                            st.success("Project created successfully!")
                            st.rerun()
                        else:
                            st.error(f"Failed to create project: {response.status_code} - {response.text}")
                    except requests.exceptions.RequestException as e:
                        st.error(f"Error creating project: {e}")
                else:
                    st.error("Project name is required.")
    
    try:
        response = requests.get(f"{API_BASE}projects/", timeout=10)
        if response.status_code == 200:
            projects = response.json()
            if projects:
                for project in projects:
                    with st.expander(f"{project.get('name', 'Unnamed')} - {project.get('owner', 'Unknown')}"):
                        st.write(f"Description: {project.get('description', 'No description')}")
                        st.write(f"Created: {project.get('created_at', 'Unknown')}")
                        if st.button(f"Delete Project {project['id']}", key=f"delete_proj_{project['id']}"):
                            try:
                                del_response = requests.delete(f"{API_BASE}projects/{project['id']}/", timeout=10)
                                if del_response.status_code == 204:
                                    st.success("Project deleted!")
                                    st.rerun()
                                else:
                                    st.error(f"Failed to delete: {del_response.status_code}")
                            except requests.exceptions.RequestException as e:
                                st.error(f"Error deleting project: {e}")
            else:
                st.write("No projects found.")
        else:
            st.error(f"Failed to fetch projects: {response.status_code}")
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {e}")

elif menu == "Tasks":
    st.header("Tasks")
    
    with st.expander("Add New Task"):
        try:
            projects_response = requests.get(f"{API_BASE}projects/", timeout=10)
            if projects_response.status_code == 200:
                projects = projects_response.json()
                project_options = {p['name']: p['id'] for p in projects}
            else:
                project_options = {}
        except:
            project_options = {}
        
        with st.form("new_task_form"):
            task_title = st.text_input("Task Title")
            task_description = st.text_area("Description")
            task_status = st.selectbox("Status", ["todo", "in_progress", "done"])
            task_priority = st.selectbox("Priority", ["low", "medium", "high"])
            selected_project = st.selectbox("Project", list(project_options.keys()) if project_options else [])
            due_date = st.date_input("Due Date", value=None)
            submitted = st.form_submit_button("Create Task")
            if submitted:
                if task_title and selected_project:
                    data = {
                        "title": task_title,
                        "description": task_description,
                        "status": task_status,
                        "priority": task_priority,
                        "project": project_options[selected_project],
                        "due_date": due_date.isoformat() if due_date else None
                    }
                    try:
                        response = requests.post(f"{API_BASE}tasks/", json=data, timeout=10)
                        if response.status_code == 201:
                            st.success("Task created successfully!")
                            st.rerun()
                        else:
                            st.error(f"Failed to create task: {response.status_code} - {response.text}")
                    except requests.exceptions.RequestException as e:
                        st.error(f"Error creating task: {e}")
                else:
                    st.error("Task title and project are required.")
    
    try:
        response = requests.get(f"{API_BASE}tasks/", timeout=10)
        if response.status_code == 200:
            tasks = response.json()
            if tasks:
                df = pd.DataFrame(tasks)
                available_cols = [col for col in ['title', 'status', 'priority', 'assigned_to', 'project'] if col in df.columns]
                st.dataframe(df[available_cols])
                
                st.subheader("Task Details")
                for task in tasks:
                    with st.expander(f"{task.get('title', 'Untitled')} - {task.get('status', 'Unknown')}"):
                        st.write(f"Description: {task.get('description', 'No description')}")
                        st.write(f"Priority: {task.get('priority', 'medium')}")
                        st.write(f"Project: {task.get('project', 'Unknown')}")
                        st.write(f"Due Date: {task.get('due_date', 'Not set')}")
                        if st.button(f"Delete Task {task['id']}", key=f"delete_task_{task['id']}"):
                            try:
                                del_response = requests.delete(f"{API_BASE}tasks/{task['id']}/", timeout=10)
                                if del_response.status_code == 204:
                                    st.success("Task deleted!")
                                    st.rerun()
                                else:
                                    st.error(f"Failed to delete: {del_response.status_code}")
                            except requests.exceptions.RequestException as e:
                                st.error(f"Error deleting task: {e}")
            else:
                st.write("No tasks found.")
        else:
            st.error(f"Failed to fetch tasks: {response.status_code}")
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {e}")

elif menu == "Users":
    st.header("Users")
    st.write("User management coming soon...")

st.markdown("---")
st.markdown("**TaskTracker** - Built with Django & Streamlit")