import React, { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import {
  ShieldCheck,
  Lock,
  History,
  LogOut,
  Sun,
  Moon,
  Activity,
  Home,
  Info,
} from "lucide-react";

const Navbar = ({
  token,
  darkMode,
  toggleDarkMode,
  handleLogout,
  triggerAuthModal,
}) => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  // Close mobile menu on outside click
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (isMenuOpen && !e.target.closest(".nav-menu-wrapper")) {
        setIsMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [isMenuOpen]);

  // Close mobile menu on viewport resize to desktop width
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth > 768) setIsMenuOpen(false);
    };
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  const navLinks = [
    { path: "/", label: "Home", Icon: Home },
    { path: "/scan", label: "Scanner", Icon: ShieldCheck },
    { path: "/history", label: "History", Icon: History },
    { path: "/dashboard", label: "Dashboard", Icon: Activity },
    { path: "/about", label: "About", Icon: Info },
  ];

  const isActive = (path) =>
    path === "/"
      ? location.pathname === "/"
      : location.pathname.startsWith(path);

  return (
    <nav className="nav-bar">
      <div className="nav-content">
        {/* Logo */}
        <button className="nav-logo" onClick={() => navigate("/")}>
          <div className="logo-icon-wrap">
            <ShieldCheck size={18} className="text-white" />
          </div>
          <span className="logo-text">ScamShield</span>
        </button>

        {/* Desktop nav links */}
        <div className="nav-links-desktop">
          {navLinks.map(({ path, label, Icon }) => (
            <button
              key={path}
              onClick={() => navigate(path)}
              className={`nav-link-btn ${isActive(path) ? "active" : ""}`}
            >
              <Icon size={15} />
              {label}
            </button>
          ))}
        </div>

        {/* Right actions */}
        <div className="nav-actions">
          {/* Theme toggle */}
          <button
            className="icon-button theme-toggle"
            onClick={toggleDarkMode}
            title="Toggle theme"
          >
            {darkMode ? <Sun size={18} /> : <Moon size={18} />}
          </button>

          {/* Auth button (desktop) */}
          <div
            className="nav-auth-desktop"
            style={{ display: "flex", gap: "8px" }}
          >
            {token ? (
              <button className="auth-chip logout" onClick={handleLogout}>
                <LogOut size={14} /> Logout
              </button>
            ) : (
              <>
                <button
                  className="auth-chip login"
                  onClick={() => triggerAuthModal("Login")}
                >
                  <Lock size={14} /> Login
                </button>
                <button
                  className="auth-chip login"
                  style={{
                    backgroundColor: "#238636",
                    borderColor: "#238636",
                  }}
                  onClick={() => navigate("/auth")}
                >
                  Sign Up
                </button>
              </>
            )}
          </div>

          {/* Hamburger (mobile only) */}
          <div className="nav-menu-wrapper">
            <button
              className={`hamburger-btn ${isMenuOpen ? "open" : ""}`}
              onClick={() => setIsMenuOpen((o) => !o)}
              aria-label="Toggle menu"
              aria-expanded={isMenuOpen}
            >
              <span className="ham-bar bar1" />
              <span className="ham-bar bar2" />
              <span className="ham-bar bar3" />
            </button>

            {/* Mobile dropdown */}
            {isMenuOpen && (
              <div className="mobile-dropdown">
                <div className="mobile-dropdown-links">
                  {navLinks.map(({ path, label, Icon }) => (
                    <button
                      key={path}
                      onClick={() => {
                        navigate(path);
                        setIsMenuOpen(false);
                      }}
                      className={`mobile-nav-item ${isActive(path) ? "active" : ""}`}
                    >
                      <Icon size={17} />
                      {label}
                      {isActive(path) && <span className="mobile-active-dot" />}
                    </button>
                  ))}
                </div>
                <div className="mobile-dropdown-divider" />
                <div className="mobile-dropdown-auth">
                  {token ? (
                    <button
                      className="mobile-auth-btn logout"
                      onClick={() => {
                        handleLogout();
                        setIsMenuOpen(false);
                      }}
                    >
                      <LogOut size={16} /> Logout
                    </button>
                  ) : (
                    <div
                      style={{
                        display: "flex",
                        flexDirection: "column",
                        gap: "10px",
                      }}
                    >
                      <button
                        className="mobile-auth-btn login"
                        onClick={() => {
                          triggerAuthModal("Login");
                          setIsMenuOpen(false);
                        }}
                      >
                        <Lock size={16} /> Login
                      </button>
                      <button
                        className="mobile-auth-btn"
                        style={{
                          backgroundColor: "#238636",
                          color: "white",
                          border: "none",
                          padding: "10px",
                          borderRadius: "6px",
                          width: "100%",
                        }}
                        onClick={() => {
                          navigate("/auth");
                          setIsMenuOpen(false);
                        }}
                      >
                        Sign Up
                      </button>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
