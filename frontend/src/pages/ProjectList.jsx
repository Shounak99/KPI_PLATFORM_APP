import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/axios';

const PER_PAGE = 6;

export default function ProjectList() {
  const [projects, setProjects] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState({ name: '', description: '' });
  const [page, setPage] = useState(1);
  const role = localStorage.getItem('role');
  const navigate = useNavigate();

  useEffect(() => {
    loadProjects();
  }, []);

  async function loadProjects() {
    const res = await api.get('/projects/');
    setProjects(res.data);
  }

  async function createProject() {
    await api.post('/projects/', form);
    setShowModal(false);
    setForm({ name: '', description: '' });
    loadProjects();
  }

  const totalPages = Math.ceil(projects.length / PER_PAGE);
  const paginated = projects.slice((page - 1) * PER_PAGE, page * PER_PAGE);

  return (
    <div className="container mt-4">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h1 className="mb-0">Projects</h1>
        {role !== 'viewer' && (
          <button className="btn btn-primary" onClick={() => setShowModal(true)}>
            + New Project
          </button>
        )}
      </div>

      <div className="row row-cols-1 row-cols-md-2 row-cols-lg-3 g-4">
        {paginated.length === 0 && (
          <div className="col-12"><p className="text-muted">No projects yet.</p></div>
        )}
        {paginated.map(p => (
          <div className="col" key={p.id}>
            <div className="card h-100 shadow-sm" style={{ cursor: 'pointer' }}
              onClick={() => navigate(`/projects/${p.id}`)}>
              <div className="card-body">
                <h5 className="card-title">{p.name}</h5>
                <p className="card-text text-muted small">{p.description}</p>
                <p className="card-text small"><strong>Owner:</strong> {p.owner_username}</p>
              </div>
              <div className="card-footer">
                <div className="d-flex gap-3 mb-2">
                  <span className="text-success">✓ {p.on_track}</span>
                  <span className="text-warning">⚠ {p.at_risk}</span>
                  <span className="text-danger">✗ {p.off_track}</span>
                  <span className="text-muted ms-auto">{p.kpi_count} KPIs</span>
                </div>
                {p.kpi_count > 0 && (
                  <span className={`badge ${
                    p.off_track > 0 ? 'bg-danger' :
                    p.at_risk > 0 ? 'bg-warning text-dark' :
                    'bg-success'
                  }`}>
                    {p.off_track > 0 ? 'Off Track' : p.at_risk > 0 ? 'At Risk' : 'On Track'}
                  </span>
                )}
                {p.kpi_count === 0 && <span className="badge bg-secondary">No KPIs</span>}
              </div>
            </div>
          </div>
        ))}
      </div>

      {totalPages > 1 && (
        <nav className="mt-4">
          <ul className="pagination">
            <li className={`page-item ${page === 1 ? 'disabled' : ''}`}>
              <button className="page-link" onClick={() => setPage(page - 1)}>Previous</button>
            </li>
            {[...Array(totalPages)].map((_, i) => (
              <li key={i} className={`page-item ${page === i + 1 ? 'active' : ''}`}>
                <button className="page-link" onClick={() => setPage(i + 1)}>{i + 1}</button>
              </li>
            ))}
            <li className={`page-item ${page === totalPages ? 'disabled' : ''}`}>
              <button className="page-link" onClick={() => setPage(page + 1)}>Next</button>
            </li>
          </ul>
        </nav>
      )}

      {showModal && (
        <div className="modal show d-block" style={{ background: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">New Project</h5>
                <button className="btn-close" onClick={() => setShowModal(false)}></button>
              </div>
              <div className="modal-body">
                <div className="mb-3">
                  <label className="form-label">Name</label>
                  <input className="form-control" value={form.name}
                    onChange={e => setForm({ ...form, name: e.target.value })} />
                </div>
                <div className="mb-3">
                  <label className="form-label">Description</label>
                  <textarea className="form-control" value={form.description}
                    onChange={e => setForm({ ...form, description: e.target.value })} />
                </div>
              </div>
              <div className="modal-footer">
                <button className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
                <button className="btn btn-primary" onClick={createProject}>Save</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
