import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import api from '../api';

const OAuthCallback = ({ setAccessToken }) => {
  const [status, setStatus] = useState('processing');
  const [error, setError] = useState(null);
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    const processOAuthCallback = async () => {
      try {
        // Parse the URL for public_token
        const params = new URLSearchParams(location.search);
        const publicToken = params.get('public_token');
        
        if (!publicToken) {
          console.error('No public_token found in URL');
          setStatus('failed');
          setError('Missing public token in the redirect URL.');
          return;
        }
        
        console.log('Public token received from OAuth redirect');
        
        // Exchange the public token for an access token
        const response = await api.post('/item/public_token/exchange', {
          public_token: publicToken
        });
        
        if (response.data.access_token) {
          console.log('Successfully exchanged public token for access token');
          setAccessToken(response.data.access_token);
          setStatus('success');
          
          // Redirect back to the main page
          setTimeout(() => {
            navigate('/');
          }, 2000);
        } else {
          console.error('No access token received:', response.data);
          setStatus('failed');
          setError('Failed to exchange token with the server.');
        }
      } catch (err) {
        console.error('Error processing OAuth callback:', err);
        setStatus('failed');
        setError(err.message || 'An unexpected error occurred.');
      }
    };
    
    processOAuthCallback();
  }, [location, navigate, setAccessToken]);

  // Render different UI based on status
  if (status === 'processing') {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <h2>Connecting to your bank...</h2>
        <div style={{ margin: '20px 0' }}>
          <div style={{ 
            width: '40px', 
            height: '40px', 
            margin: '0 auto',
            border: '4px solid #f3f3f3',
            borderTop: '4px solid #3498db',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite'
          }} />
        </div>
        <p>Please wait while we complete your bank connection.</p>
        <style>{`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    );
  }
  
  if (status === 'success') {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <h2 style={{ color: '#2e7d32' }}>Successfully Connected!</h2>
        <p>Your bank account has been connected successfully.</p>
        <p>Redirecting you back...</p>
      </div>
    );
  }
  
  if (status === 'failed') {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <h2 style={{ color: '#d32f2f' }}>Connection Failed</h2>
        <p>{error || 'There was a problem connecting to your bank.'}</p>
        <button 
          onClick={() => navigate('/')}
          style={{
            padding: '10px 15px',
            backgroundColor: '#2196f3',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            marginTop: '20px'
          }}
        >
          Back to Home
        </button>
      </div>
    );
  }
  
  return null;
};

export default OAuthCallback;
