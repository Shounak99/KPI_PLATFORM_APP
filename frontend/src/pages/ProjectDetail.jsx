import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../api/axios';

export default function ProjectDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const role = localStorage.getItem('role');
  const username = localStorage.getItem('username');

  const [project, setProject] = useState(null);
  const [kpis, setKpis] = useState([]);
  const [showKpiModal, setShowKpiModal] = useState(false);
  const [editingKpi, setEditingKpi] = useState(null);
  const [kpiForm, setKpiForm] = useState({ name: '', description: '', unit: '', target_value: '', actual_value: '', status: 'on_track' });

  useEffect(() => {
    loadProject();
    loadKpis();
  }, [id]);

  async function loadProject() {
    const res = await api.get(`/projects/${id}/`);
    setProject(res.data);
  }

  async function loadKpis() {
    let results = [];
    let url = `/projects/${id}/kpis/`;
    while (url) {
      const res = await api.get(url);
      results = [...results, ...res.data.results];
      url = res.data.next;
    }
    setKpis(results);
  }

  async function deleteProject() {
    if (!confirm('Delete this project and all its KPIs?')) return;
    await api.delete(`/projects/${id}/`);
    navigate('/projects');
  }

  async function saveKpi() {
    if (editingKpi) {
      await api.put(`/projects/${id}/kpis/${editingKpi.id}/`, kpiForm);
    } else {
      await api.post(`/projects/${id}/kpis/`, kpiForm);
    }
    setShowKpiModal(false);
    setEditingKpi(null);
    setKpiForm({ name: '', description: '', unit: '', target_value: '', actual_value: '', status: 'on_track' });
    loadKpis();
  }

  async function deleteKpi(kpiId) {
    if (!confirm('Delete this KPI?')) return;
    await api.delete(`/projects/${id}/kpis/${kpiId}/`);
    loadKpis();
  }

  function openEditKpi(kpi) {
    setEditingKpi(kpi);
    setKpiForm({ name: kpi.name, description: kpi.description, unit: kpi.unit,
      target_value: kpi.target_value, actual_value: kpi.actual_value, status: kpi.status });
    setShowKpiModal(true);
  }

  const canEdit = role === 'admin' || project?.owner_username === username;

  if (!project) return <div className="container mt-4">Loading...</div>;

  return (
    <div className="container mt-4">
      <div className="d-flex justify-content-between align-items-start mb-4">
        <div>
          <h1 className="mb-1">{project.name}</h1>
          <p className="text-muted mb-1">{project.description}</p>
          <p className="text-muted small"><strong>Owner:</strong> {project.owner_username}</p>
        </div>
        {canEdit && (
          <div className="d-flex gap-2">
            <button className="btn btn-outline-danger btn-sm" onClick={deleteProject}>Delete</button>
          </div>
        )}
      </div>

      <div className="d-flex justify-content-between align-items-center mb-3">
        <h4 className="mb-0">KPIs</h4>
        {canEdit && (
          <button className="btn btn-primary btn-sm" onClick={() => setShowKpiModal(true)}>+ Add KPI</button>
        )}
      </div>

      <div className="row row-cols-1 row-cols-md-2 row-cols-lg-3 g-4">
        {kpis.length === 0 && (
          <div className="col-12"><p className="text-muted">No KPIs yet.</p></div>
        )}
        {kpis.map(kpi => (
          <div className="col" key={kpi.id}>
            <div className="card h-100 shadow-sm">
              <div className="card-body">
                <h6 className="card-title">{kpi.name}</h6>
                <p className="card-text text-muted small">{kpi.description}</p>
                <div className="mb-2">
                  <div className="d-flex justify-content-between small mb-1">
                    <span>{kpi.actual_value} / {kpi.target_value} {kpi.unit}</span>
                    <span>{kpi.progress_percent}%</span>
                  </div>
                  <div className="progress" style={{ height: '8px' }}>
                    <div className={`progress-bar ${kpi.status === 'on_track' ? 'bg-success' : kpi.status === 'at_risk' ? 'bg-warning' : 'bg-danger'}`}
                      style={{ width: `${kpi.progress_percent}%` }} />
                  </div>
                </div>
                <span className={`badge ${kpi.status === 'on_track' ? 'bg-success' : kpi.status === 'at_risk' ? 'bg-warning text-dark' : 'bg-danger'}`}>
                  {kpi.status.replace('_', ' ')}
                </span>
              </div>
              {canEdit && (
                <div className="card-footer d-flex gap-2">
                  <button className="btn btn-outline-secondary btn-sm" onClick={() => openEditKpi(kpi)}>Edit</button>
                  <button className="btn btn-outline-danger btn-sm" onClick={() => deleteKpi(kpi.id)}>Delete</button>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      <button className="btn btn-link mt-4 ps-0" onClick={() => navigate('/projects')}>← Back to Projects</button>

      {showKpiModal && (
        <div className="modal show d-block" style={{ background: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">{editingKpi ? 'Edit KPI' : 'New KPI'}</h5>
                <button className="btn-close" onClick={() => { setShowKpiModal(false); setEditingKpi(null); }}></button>
              </div>
              <div className="modal-body">
                {['name', 'description', 'unit'].map(field => (
                  <div className="mb-3" key={field}>
                    <label className="form-label text-capitalize">{field}</label>
                    <input className="form-control" value={kpiForm[field]}
                      onChange={e => setKpiForm({ ...kpiForm, [field]: e.target.value })} />
                  </div>
                ))}
                <div className="mb-3">
                  <label className="form-label">Target Value</label>
                  <input type="number" className="form-control" value={kpiForm.target_value}
                    onChange={e => setKpiForm({ ...kpiForm, target_value: e.target.value })} />
                </div>
                <div className="mb-3">
                  <label className="form-label">Actual Value</label>
                  <input type="number" className="form-control" value={kpiForm.actual_value}
                    onChange={e => setKpiForm({ ...kpiForm, actual_value: e.target.value })} />
                </div>
                <div className="mb-3">
                  <label className="form-label">Status</label>
                  <select className="form-select" value={kpiForm.status}
                    onChange={e => setKpiForm({ ...kpiForm, status: e.target.value })}>
                    <option value="on_track">On Track</option>
                    <option value="at_risk">At Risk</option>
                    <option value="off_track">Off Track</option>
                  </select>
                </div>
              </div>
              <div className="modal-footer">
                <button className="btn btn-secondary" onClick={() => { setShowKpiModal(false); setEditingKpi(null); }}>Cancel</button>
                <button className="btn btn-primary" onClick={saveKpi}>Save</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
