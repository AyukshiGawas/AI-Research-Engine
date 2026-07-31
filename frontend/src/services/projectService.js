import api from './api';

export const projectService = {
  async getProjects() {
    const response = await api.get('/projects/');
    return response.data;
  },

  async createProject(projectData) {
    const response = await api.post('/projects/', projectData);
    return response.data;
  },
};
