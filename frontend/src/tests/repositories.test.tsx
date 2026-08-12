import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from '../context/AuthContext';
import { ToastProvider } from '../components/Toast';
import ProtectedRoute from '../components/ProtectedRoute';
import DashboardLayout from '../layouts/DashboardLayout';
import RepositoriesPage from '../pages/RepositoriesPage';
import RepositoryDetailPage from '../pages/RepositoryDetailPage';
import { Repository } from '../types';

vi.mock('../services/auth', () => ({
  default: {
    getToken: vi.fn(() => 'fake-token'),
    getCurrentUser: vi.fn(async () => ({
      id: 'user-1',
      name: 'Test User',
      email: 'test@example.com',
      is_active: true,
      created_at: '2026-08-01T00:00:00Z',
    })),
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
  },
}));

vi.mock('../services/repositories', () => ({
  default: {
    list: vi.fn(),
    get: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    remove: vi.fn(),
  },
}));

import authService from '../services/auth';
import repositoryService from '../services/repositories';

const mockedRepoService = vi.mocked(repositoryService);
const mockedAuthService = vi.mocked(authService);

const sampleRepo: Repository = {
  id: 'repo-1',
  name: 'backend-api',
  url: 'https://github.com/example/backend-api',
  provider: 'github',
  default_branch: 'main',
  description: 'Backend API',
  is_active: true,
  last_scan_at: null,
  created_at: '2026-08-10T00:00:00Z',
  updated_at: '2026-08-10T00:00:00Z',
};

function renderApp(initialPath: string) {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <AuthProvider>
        <ToastProvider>
          <Routes>
            <Route path="/login" element={<div>Login Page</div>} />
            <Route element={<ProtectedRoute />}>
              <Route element={<DashboardLayout />}>
                <Route path="/repositories" element={<RepositoriesPage />} />
                <Route path="/repositories/:id" element={<RepositoryDetailPage />} />
              </Route>
            </Route>
          </Routes>
        </ToastProvider>
      </AuthProvider>
    </MemoryRouter>
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  mockedAuthService.getToken.mockReturnValue('fake-token');
  mockedAuthService.getCurrentUser.mockResolvedValue({
    id: 'user-1',
    name: 'Test User',
    email: 'test@example.com',
    is_active: true,
    created_at: '2026-08-01T00:00:00Z',
  });
});

describe('RepositoriesPage', () => {
  it('renders the repository list', async () => {
    mockedRepoService.list.mockResolvedValue([sampleRepo]);
    renderApp('/repositories');

    expect(await screen.findByText('backend-api')).toBeInTheDocument();
    expect(screen.getByText('github.com/example/backend-api')).toBeInTheDocument();
    expect(screen.getByText('GitHub')).toBeInTheDocument();
    expect(screen.getByText('main')).toBeInTheDocument();
    expect(screen.getByText('Never')).toBeInTheDocument();
  });

  it('shows the empty state when there are no repositories', async () => {
    mockedRepoService.list.mockResolvedValue([]);
    renderApp('/repositories');

    expect(
      await screen.findByText('No repositories connected yet.')
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Connect your first repository to start/)
    ).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Add Repository/i })).toBeInTheDocument();
  });

  it('opens the add repository form and creates a repository', async () => {
    const user = userEvent.setup();
    mockedRepoService.list.mockResolvedValue([]);
    mockedRepoService.create.mockResolvedValue(sampleRepo);
    renderApp('/repositories');

    await user.click(await screen.findByRole('button', { name: /Add Repository/i }));

    const dialog = await screen.findByRole('dialog', { name: 'Add Repository' });
    expect(dialog).toBeInTheDocument();

    await user.type(within(dialog).getByLabelText('Repository Name'), 'backend-api');
    await user.type(
      within(dialog).getByLabelText('Repository URL'),
      'https://github.com/example/backend-api'
    );
    await user.click(within(dialog).getByRole('button', { name: 'Add Repository' }));

    await waitFor(() => {
      expect(mockedRepoService.create).toHaveBeenCalledWith({
        name: 'backend-api',
        url: 'https://github.com/example/backend-api',
        provider: 'github',
        default_branch: 'main',
      });
    });

    // Repository is displayed after creation
    expect(await screen.findByText('backend-api')).toBeInTheDocument();
    expect(screen.queryByRole('dialog', { name: 'Add Repository' })).not.toBeInTheDocument();
  });

  it('shows a validation error for an invalid repository URL', async () => {
    const user = userEvent.setup();
    mockedRepoService.list.mockResolvedValue([]);
    renderApp('/repositories');

    await user.click(await screen.findByRole('button', { name: /Add Repository/i }));
    const dialog = await screen.findByRole('dialog', { name: 'Add Repository' });

    await user.type(within(dialog).getByLabelText('Repository Name'), 'backend-api');
    await user.type(within(dialog).getByLabelText('Repository URL'), 'not-a-valid-url');
    await user.click(within(dialog).getByRole('button', { name: 'Add Repository' }));

    expect(
      await screen.findByText(/Please enter a valid GitHub repository URL/)
    ).toBeInTheDocument();
    expect(mockedRepoService.create).not.toHaveBeenCalled();
  });

  it('shows a validation error when the name is missing', async () => {
    const user = userEvent.setup();
    mockedRepoService.list.mockResolvedValue([]);
    renderApp('/repositories');

    await user.click(await screen.findByRole('button', { name: /Add Repository/i }));
    const dialog = await screen.findByRole('dialog', { name: 'Add Repository' });

    await user.type(
      within(dialog).getByLabelText('Repository URL'),
      'https://github.com/example/backend-api'
    );
    await user.click(within(dialog).getByRole('button', { name: 'Add Repository' }));

    expect(await screen.findByText('Repository name is required.')).toBeInTheDocument();
    expect(mockedRepoService.create).not.toHaveBeenCalled();
  });

  it('edits a repository', async () => {
    const user = userEvent.setup();
    mockedRepoService.list.mockResolvedValue([sampleRepo]);
    mockedRepoService.update.mockResolvedValue({
      ...sampleRepo,
      name: 'renamed-repo',
    });
    renderApp('/repositories');

    await user.click(await screen.findByRole('button', { name: /Edit/i }));
    await screen.findByRole('dialog', { name: 'Edit Repository' });

    const nameInput = screen.getByLabelText('Repository Name');
    await user.clear(nameInput);
    await user.type(nameInput, 'renamed-repo');
    await user.click(screen.getByRole('button', { name: 'Save Changes' }));

    await waitFor(() => {
      expect(mockedRepoService.update).toHaveBeenCalledWith('repo-1', {
        name: 'renamed-repo',
        default_branch: 'main',
        description: 'Backend API',
        is_active: true,
      });
    });

    expect(await screen.findByText('renamed-repo')).toBeInTheDocument();
  });

  it('shows a delete confirmation dialog before deleting', async () => {
    const user = userEvent.setup();
    mockedRepoService.list.mockResolvedValue([sampleRepo]);
    renderApp('/repositories');

    await user.click(await screen.findByRole('button', { name: /Delete/i }));

    expect(await screen.findByText('Delete Repository?')).toBeInTheDocument();
    expect(screen.getByText(/Are you sure you want to remove/)).toBeInTheDocument();
    expect(screen.getByText('This action cannot be undone.')).toBeInTheDocument();
    expect(mockedRepoService.remove).not.toHaveBeenCalled();

    // Cancel keeps the repository
    await user.click(screen.getByRole('button', { name: 'Cancel' }));
    expect(screen.queryByText('Delete Repository?')).not.toBeInTheDocument();
    expect(screen.getByText('backend-api')).toBeInTheDocument();
  });

  it('deletes a repository after confirmation', async () => {
    const user = userEvent.setup();
    mockedRepoService.list.mockResolvedValue([sampleRepo]);
    mockedRepoService.remove.mockResolvedValue({
      message: 'Repository deleted successfully',
    });
    renderApp('/repositories');

    await user.click(await screen.findByRole('button', { name: /Delete/i }));
    await screen.findByText('Delete Repository?');
    await user.click(screen.getByRole('button', { name: 'Delete Repository' }));

    await waitFor(() => {
      expect(mockedRepoService.remove).toHaveBeenCalledWith('repo-1');
    });

    expect(
      await screen.findByText('No repositories connected yet.')
    ).toBeInTheDocument();
    expect(screen.queryByText('github.com/example/backend-api')).not.toBeInTheDocument();
  });

  it('redirects unauthorized users to login', async () => {
    mockedAuthService.getToken.mockReturnValue(null);
    mockedRepoService.list.mockResolvedValue([]);
    renderApp('/repositories');

    expect(await screen.findByText('Login Page')).toBeInTheDocument();
    expect(mockedRepoService.list).not.toHaveBeenCalled();
  });
});

describe('RepositoryDetailPage', () => {
  it('renders repository details with a disabled scan button', async () => {
    mockedRepoService.get.mockResolvedValue(sampleRepo);
    renderApp('/repositories/repo-1');

    expect(await screen.findByText('backend-api')).toBeInTheDocument();
    expect(screen.getByText('https://github.com/example/backend-api')).toBeInTheDocument();
    expect(screen.getByText('main')).toBeInTheDocument();
    expect(screen.getByText('Never')).toBeInTheDocument();

    const scanButton = screen.getByRole('button', { name: /Scan Repository/i });
    expect(scanButton).toBeDisabled();
    expect(
      screen.getByText('Repository scanning will be available in the next version.')
    ).toBeInTheDocument();
  });

  it('shows not found for an inaccessible repository', async () => {
    mockedRepoService.get.mockRejectedValue(new Error('404'));
    renderApp('/repositories/unknown-id');

    expect(await screen.findByText('Repository not found')).toBeInTheDocument();
  });
});
