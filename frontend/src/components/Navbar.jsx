import { Link, useNavigate } from "react-router-dom";

export default function Navbar() {
  const navigate = useNavigate();
  const username = localStorage.getItem("username");
  const role = localStorage.getItem("role");

  function handleLogout() {
    localStorage.clear();
    navigate("/login");
  }

  return (
    <nav className="navbar navbar-expand-lg navbar-dark bg-dark">
      <div className="container">
        <Link className="navbar-brand" to="/projects">
          KPI Platform
        </Link>
        <Link className="nav-link text-light" to="/kpis">
          All KPIs
        </Link>

        <div className="ms-auto d-flex align-items-center gap-3">
          {username && (
            <>
              <span className="text-light small">
                {username} ({role})
              </span>
              <button
                className="btn btn-outline-light btn-sm"
                onClick={handleLogout}
              >
                Logout
              </button>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}
