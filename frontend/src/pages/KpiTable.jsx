import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/axios';

async function fetchAllPages(url) {
  let results = [];
  let next = url;
  while (next) {
    const res = await api.get(next);
    results = [...results, ...res.data.results];
    next = res.data.next;
  }
  return results;
}

export default function KpiTable() {
  const [kpis, setKpis] = useState([]);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const perPage = 10;
  const navigate = useNavigate();

  useEffect(() => {
    loadAll();
  }, []);

  async function loadAll() {
    const allProjects = await fetchAllPages('/projects/');
    const allKpis = [];
    for (const project of allProjects) {
      const kpis = await fetchAllPages(`/projects/${project.id}/kpis/`);
      kpis.forEach(k => allKpis.push({ ...k, project_name: project.name, project_id: project.id }));
    }
    setKpis(allKpis);
  }

  const filtered = kpis.filter(k => {
    const matchSearch = k.name.toLowerCase().includes(search.toLowerCase()) ||
      k.project_name.toLowerCase().includes(search.toLowerCase());
    const matchStatus = statusFilter ? k.status === statusFilter : true;
    return matchSearch && matchStatus;
  });

  const totalPages = Math.ceil(filtered.length / perPage);
  const paginated = filtered.slice((page - 1) * perPage, page * perPage);

  function statusBadge(status) {
    const map = { on_track: 'success', at_risk: 'warning', off_track: 'danger' };
    return <span className={`badge bg-${map[status]} ${status === 'at_risk' ? 'text-dark' : ''}`}>
      {status.replace('_', ' ')}
    </span>;
  }

  return (
    <div className="container mt-4">
      <h1 className="mb-4">All KPIs</h1>

      <div className="row mb-3 g-2">
        <div className="col-md-6">
          <input className="form-control" placeholder="Search by KPI or project name..."
            value={search} onChange={e => { setSearch(e.target.value); setPage(1); }} />
        </div>
        <div className="col-md-3">
          <select className="form-select" value={statusFilter}
            onChange={e => { setStatusFilter(e.target.value); setPage(1); }}>
            <option value="">All Statuses</option>
            <option value="on_track">On Track</option>
            <option value="at_risk">At Risk</option>
            <option value="off_track">Off Track</option>
          </select>
        </div>
        <div className="col-md-3 d-flex align-items-center text-muted small">
          {filtered.length} KPIs found
        </div>
      </div>

      <div className="table-responsive">
        <table className="table table-hover table-bordered">
          <thead className="table-dark">
            <tr>
              <th>KPI Name</th>
              <th>Project</th>
              <th>Target</th>
              <th>Actual</th>
              <th>Unit</th>
              <th>Progress</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {paginated.length === 0 && (
              <tr><td colSpan="7" className="text-center text-muted">No KPIs found.</td></tr>
            )}
            {paginated.map(kpi => (
              <tr key={kpi.id} style={{ cursor: 'pointer' }}
                onClick={() => navigate(`/projects/${kpi.project_id}`)}>
                <td>{kpi.name}</td>
                <td>{kpi.project_name}</td>
                <td>{kpi.target_value}</td>
                <td>{kpi.actual_value}</td>
                <td>{kpi.unit}</td>
                <td>
                  <div className="progress" style={{ height: '8px', minWidth: '80px' }}>
                    <div className={`progress-bar ${kpi.status === 'on_track' ? 'bg-success' : kpi.status === 'at_risk' ? 'bg-warning' : 'bg-danger'}`}
                      style={{ width: `${kpi.progress_percent}%` }} />
                  </div>
                  <small>{kpi.progress_percent}%</small>
                </td>
                <td>{statusBadge(kpi.status)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <nav>
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
    </div>
  );
}
