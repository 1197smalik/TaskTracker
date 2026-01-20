const DEFAULT_API_BASE = 'https://api-tasktracker.shubhammalik.com/api';

const state = {
  apiBase: DEFAULT_API_BASE,
  projects: [],
  tasks: [],
  activeView: 'dashboard',
  projectFilter: 'all',
  searchTerm: '',
};

const statusLabels = {
  todo: 'To Do',
  in_progress: 'In Progress',
  done: 'Done',
};

const priorityLabels = {
  low: 'Low',
  medium: 'Medium',
  high: 'High',
};

const views = {
  dashboard: document.getElementById('dashboardView'),
  projects: document.getElementById('projectsView'),
  tasks: document.getElementById('tasksView'),
};

const apiStatusEl = document.getElementById('apiStatus');
const statusDot = document.querySelector('.status-dot');
const viewTitle = document.getElementById('viewTitle');
const projectsGrid = document.getElementById('projectsGrid');
const taskBoard = document.getElementById('taskBoard');
const projectFilter = document.getElementById('projectFilter');

const modal = document.getElementById('modal');
const modalTitle = document.getElementById('modalTitle');
const modalFields = document.getElementById('modalFields');
const modalForm = document.getElementById('modalForm');


function buildUrl(path) {
  const base = state.apiBase.replace(/\/$/, '');
  const suffix = path.replace(/^\//, '');
  return `${base}/${suffix}`;
}

async function requestJson(path, options = {}) {
  const response = await fetch(buildUrl(path), {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed with ${response.status}`);
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

async function checkApi() {
  try {
    await requestJson('/projects/');
    apiStatusEl.textContent = 'Connected';
    statusDot.style.background = 'var(--success)';
  } catch (error) {
    apiStatusEl.textContent = 'Offline';
    statusDot.style.background = 'var(--danger)';
  }
}

async function loadData() {
  await checkApi();
  state.projects = await requestJson('/projects/');
  state.tasks = await requestJson('/tasks/');
  renderDashboard();
  renderProjects();
  renderTasks();
}

function renderDashboard() {
  const totalProjects = state.projects.length;
  const totalTasks = state.tasks.length;
  const inProgress = state.tasks.filter((task) => task.status === 'in_progress').length;

  document.getElementById('metricProjects').textContent = totalProjects;
  document.getElementById('metricTasks').textContent = totalTasks;
  document.getElementById('metricInProgress').textContent = inProgress;
}

function renderProjects() {
  projectsGrid.innerHTML = '';

  if (!state.projects.length) {
    projectsGrid.innerHTML = '<p>No projects yet.</p>';
    return;
  }

  state.projects.forEach((project) => {
    const card = document.createElement('div');
    card.className = 'card';
    card.innerHTML = `
      <div>
        <h3>${escapeHtml(project.name || 'Untitled')}</h3>
        <p>${escapeHtml(project.description || 'No description')}</p>
      </div>
      <div class="card-meta">
        <span>Owner: ${escapeHtml(String(project.owner ?? 'Unassigned'))}</span>
        <span>Members: ${(project.members || []).length}</span>
      </div>
      <div class="card-actions">
        <button class="ghost" data-action="edit-project" data-id="${project.id}">Edit</button>
        <button class="ghost" data-action="delete-project" data-id="${project.id}">Delete</button>
      </div>
    `;
    projectsGrid.appendChild(card);
  });
}

function renderTasks() {
  const columns = ['todo', 'in_progress', 'done'];
  taskBoard.innerHTML = '';

  const filteredTasks = state.tasks.filter((task) => {
    const matchesProject =
      state.projectFilter === 'all' || String(task.project) === state.projectFilter;
    const text = `${task.title || ''} ${task.description || ''}`.toLowerCase();
    const matchesSearch = text.includes(state.searchTerm.toLowerCase());
    return matchesProject && matchesSearch;
  });

  columns.forEach((status) => {
    const column = document.createElement('div');
    column.className = 'column';
    const tasks = filteredTasks.filter((task) => task.status === status);

    const tasksHtml = tasks
      .map((task) => renderTaskCard(task))
      .join('');

    column.innerHTML = `
      <div class="column-header">
        <div class="column-title">${statusLabels[status]}</div>
        <div>${tasks.length}</div>
      </div>
      <div class="column-body">${tasksHtml || '<p>No tasks</p>'}</div>
    `;

    taskBoard.appendChild(column);
  });
}

function renderTaskCard(task) {
  const project = state.projects.find((proj) => proj.id === task.project);
  const projectName = project ? project.name : 'Unassigned';

  return `
    <div class="card-task">
      <strong>${escapeHtml(task.title || 'Untitled')}</strong>
      <span>${escapeHtml(projectName)}</span>
      <span class="badge ${task.priority || 'medium'}">${priorityLabels[task.priority] || 'Medium'}</span>
      <div class="card-actions">
        <button class="ghost" data-action="edit-task" data-id="${task.id}">Edit</button>
        <button class="ghost" data-action="delete-task" data-id="${task.id}">Delete</button>
      </div>
    </div>
  `;
}

function refreshProjectFilter() {
  projectFilter.innerHTML = '<option value="all">All projects</option>';
  state.projects.forEach((project) => {
    const option = document.createElement('option');
    option.value = String(project.id);
    option.textContent = project.name || 'Untitled';
    projectFilter.appendChild(option);
  });
}

function setActiveView(view) {
  state.activeView = view;
  Object.keys(views).forEach((key) => {
    views[key].classList.toggle('hidden', key !== view);
  });
  document.querySelectorAll('.nav-item').forEach((button) => {
    button.classList.toggle('is-active', button.dataset.view === view);
  });
  viewTitle.textContent = view.charAt(0).toUpperCase() + view.slice(1);
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function openModal(config) {
  modalTitle.textContent = config.title;
  modalFields.innerHTML = '';

  config.fields.forEach((field) => {
    const wrapper = document.createElement('label');
    wrapper.className = 'field';
    const label = document.createElement('span');
    label.textContent = field.label;
    wrapper.appendChild(label);

    let input;
    if (field.type === 'textarea') {
      input = document.createElement('textarea');
    } else if (field.type === 'select') {
      input = document.createElement('select');
      field.options.forEach((option) => {
        const opt = document.createElement('option');
        opt.value = option.value;
        opt.textContent = option.label;
        input.appendChild(opt);
      });
    } else {
      input = document.createElement('input');
      input.type = field.type || 'text';
    }

    input.name = field.name;
    if (field.value !== undefined && field.value !== null) {
      input.value = field.value;
    }

    wrapper.appendChild(input);
    modalFields.appendChild(wrapper);
  });

  modalForm.onsubmit = async (event) => {
    event.preventDefault();
    const data = Object.fromEntries(new FormData(modalForm).entries());
    await config.onSubmit(data);
  };

  modal.classList.remove('hidden');
}

function closeModal() {
  modal.classList.add('hidden');
}

async function createProject(data) {
  const payload = {
    name: data.name,
    description: data.description,
    members: [],
  };
  if (data.owner) {
    payload.owner = Number(data.owner);
  }
  await requestJson('/projects/', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  await loadData();
}

async function updateProject(id, data) {
  const payload = {
    name: data.name,
    description: data.description,
    members: [],
  };
  if (data.owner) {
    payload.owner = Number(data.owner);
  }
  await requestJson(`/projects/${id}/`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
  await loadData();
}

async function deleteProject(id) {
  if (!confirm('Delete this project?')) return;
  await requestJson(`/projects/${id}/`, { method: 'DELETE' });
  await loadData();
}

async function createTask(data) {
  await requestJson('/tasks/', {
    method: 'POST',
    body: JSON.stringify({
      title: data.title,
      description: data.description,
      status: data.status,
      priority: data.priority,
      project: Number(data.project),
      due_date: data.due_date || null,
    }),
  });
  await loadData();
}

async function updateTask(id, data) {
  await requestJson(`/tasks/${id}/`, {
    method: 'PUT',
    body: JSON.stringify({
      title: data.title,
      description: data.description,
      status: data.status,
      priority: data.priority,
      project: Number(data.project),
      due_date: data.due_date || null,
    }),
  });
  await loadData();
}

async function deleteTask(id) {
  if (!confirm('Delete this task?')) return;
  await requestJson(`/tasks/${id}/`, { method: 'DELETE' });
  await loadData();
}

function openProjectModal(mode, project) {
  openModal({
    title: mode === 'create' ? 'New Project' : 'Edit Project',
    fields: [
      { label: 'Project name', name: 'name', value: project?.name || '' },
      { label: 'Description', name: 'description', type: 'textarea', value: project?.description || '' },
    ],
    onSubmit: async (data) => {
      if (mode === 'create') {
        await createProject(data);
      } else {
        await updateProject(project.id, data);
      }
      closeModal();
    },
  });
}

function openTaskModal(mode, task) {
  const projectOptions = state.projects.map((project) => ({
    value: String(project.id),
    label: project.name || 'Untitled',
  }));

  openModal({
    title: mode === 'create' ? 'New Task' : 'Edit Task',
    fields: [
      { label: 'Title', name: 'title', value: task?.title || '' },
      { label: 'Description', name: 'description', type: 'textarea', value: task?.description || '' },
      {
        label: 'Status',
        name: 'status',
        type: 'select',
        options: [
          { value: 'todo', label: statusLabels.todo },
          { value: 'in_progress', label: statusLabels.in_progress },
          { value: 'done', label: statusLabels.done },
        ],
        value: task?.status || 'todo',
      },
      {
        label: 'Priority',
        name: 'priority',
        type: 'select',
        options: [
          { value: 'low', label: priorityLabels.low },
          { value: 'medium', label: priorityLabels.medium },
          { value: 'high', label: priorityLabels.high },
        ],
        value: task?.priority || 'medium',
      },
      {
        label: 'Project',
        name: 'project',
        type: 'select',
        options: projectOptions,
        value: task?.project ? String(task.project) : (projectOptions[0]?.value || ''),
      },
      { label: 'Due date', name: 'due_date', type: 'date', value: task?.due_date || '' },
    ],
    onSubmit: async (data) => {
      if (mode === 'create') {
        await createTask(data);
      } else {
        await updateTask(task.id, data);
      }
      closeModal();
    },
  });
}

function bindEvents() {
  document.querySelectorAll('.nav-item').forEach((button) => {
    button.addEventListener('click', () => setActiveView(button.dataset.view));
  });

  document.getElementById('refreshBtn').addEventListener('click', loadData);
  document.getElementById('newProjectBtn').addEventListener('click', () => openProjectModal('create'));
  document.getElementById('newTaskBtn').addEventListener('click', () => openTaskModal('create'));

  document.getElementById('closeModal').addEventListener('click', closeModal);
  document.getElementById('cancelModal').addEventListener('click', closeModal);
  modal.addEventListener('click', (event) => {
    if (event.target === modal) closeModal();
  });

  projectFilter.addEventListener('change', (event) => {
    state.projectFilter = event.target.value;
    renderTasks();
  });

  document.getElementById('clearFilter').addEventListener('click', () => {
    state.projectFilter = 'all';
    projectFilter.value = 'all';
    renderTasks();
  });

  document.getElementById('searchInput').addEventListener('input', (event) => {
    state.searchTerm = event.target.value;
    renderTasks();
  });

  projectsGrid.addEventListener('click', (event) => {
    const button = event.target.closest('button');
    if (!button) return;
    const action = button.dataset.action;
    const id = button.dataset.id;
    const project = state.projects.find((item) => String(item.id) === id);

    if (action === 'edit-project') {
      openProjectModal('edit', project);
    }

    if (action === 'delete-project') {
      deleteProject(id);
    }
  });

  taskBoard.addEventListener('click', (event) => {
    const button = event.target.closest('button');
    if (!button) return;
    const action = button.dataset.action;
    const id = button.dataset.id;
    const task = state.tasks.find((item) => String(item.id) === id);

    if (action === 'edit-task') {
      openTaskModal('edit', task);
    }

    if (action === 'delete-task') {
      deleteTask(id);
    }
  });
}

async function init() {
  refreshProjectFilter();
  bindEvents();
  await loadData();
  refreshProjectFilter();
  setActiveView('dashboard');
}

init();
