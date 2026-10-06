import React, { useState } from 'react';
import { GoogleLogin } from '@react-oauth/google';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import './AuthPage.css';
import { API_URL } from '../config';

// We accept onLogin as a prop so we can tell App.jsx that the user logged in
const AuthPage = ({ onLogin }) => {
  const [isLogin, setIsLogin] = useState(true);
  
  // State for the manual email/password form
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  
  const navigate = useNavigate();

  // 1. Handle Google Authentication
  const handleGoogleSuccess = async (credentialResponse) => {
    try {
      const res = await fetch(`${API_URL}/auth/google-login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: credentialResponse.credential }),
      });
      
      if (!res.ok) throw new Error("Google authentication failed on backend");
      
      const data = await res.json();
      
      // --- UPDATE HERE ---
      if (onLogin) {
        onLogin(data.access_token, data.user); 
      } else {
        localStorage.setItem("scamshield_token", data.access_token);
        localStorage.setItem("scamshield_user", JSON.stringify(data.user)); // Store user!
      }
      
      toast.success('Successfully logged in with Google!');
      navigate('/dashboard');
    } catch (error) {
      console.error('Error authenticating with backend', error);
      toast.error('Google login failed.');
    }
  };

  // 2. Handle Standard Email/Password Authentication
  const handleEmailSubmit = async (e) => {
    e.preventDefault();
    
    try {
      if (isLogin) {
        // FastAPI OAuth2PasswordRequestForm expects form-urlencoded data
        const fd = new URLSearchParams();
        fd.append("username", email);
        fd.append("password", password);
        
        const res = await fetch(`${API_URL}/login`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
          body: fd,
        });

        const data = await res.json();
        
        if (!res.ok) {
          throw new Error(data.detail || "Authentication failed. Check your credentials.");
        }
        
        if (onLogin) {
          onLogin(data.access_token, data.user);
        } else {
          localStorage.setItem("scamshield_token", data.access_token);
          localStorage.setItem("scamshield_user", JSON.stringify(data.user));
        }
        
        toast.success('Logged in successfully!');
        navigate('/dashboard');
        
      } else {
        // Registration Flow
        const res = await fetch(`${API_URL}/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password, full_name: fullName }),
        });
        
        const data = await res.json();
        if (!res.ok) {
          throw new Error(data.detail || "Registration failed");
        }
        
        toast.success('Account created! Please sign in.');
        setIsLogin(true); // Switch back to login view
        setPassword('');  // Clear password for security
      }
    } catch (error) {
      console.error('Auth error', error);
      toast.error(error.message || 'Authentication failed. Check your credentials.');
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h2 className="auth-title">
          {isLogin ? 'Sign in to ScamShield' : 'Create an Account'}
        </h2>
        <p className="auth-subtitle">
          {isLogin ? 'Welcome back to your dashboard.' : 'Join to track your scan history.'}
        </p>

        <div className="google-btn-wrapper">
          <GoogleLogin
            onSuccess={handleGoogleSuccess}
            onError={() => {
              console.log('Google Login Failed');
              toast.error('Google login window closed or failed.');
            }}
            theme="filled_black"
            shape="rectangular"
            size="large"
            width="100%"
          />
        </div>

        <div className="divider">
          <span>OR CONTINUE WITH EMAIL</span>
        </div>

        <form className="auth-form" onSubmit={handleEmailSubmit}>
          {!isLogin && (
            <input 
              type="text" 
              placeholder="Full Name" 
              className="auth-input" 
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              required
            />
          )}
          <input 
            type="email" 
            placeholder="Email Address" 
            className="auth-input" 
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <input 
            type="password" 
            placeholder="Password" 
            className="auth-input" 
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          
          <button type="submit" className="auth-submit-btn">
            {isLogin ? 'Sign In' : 'Sign Up'}
          </button>
        </form>

        <p className="auth-toggle">
          {isLogin ? "Don't have an account? " : "Already have an account? "}
          <span onClick={() => setIsLogin(!isLogin)}>
            {isLogin ? 'Sign up' : 'Log in'}
          </span>
        </p>
      </div>
    </div>
  );
};

export default AuthPage;