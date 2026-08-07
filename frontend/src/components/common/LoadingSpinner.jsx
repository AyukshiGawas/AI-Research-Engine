import React from 'react';

export const LoadingSpinner = ({ size = 'medium', message = 'Loading...' }) => {
  const sizeMap = {
    small: 16,
    medium: 24,
    large: 36,
  };

  const px = sizeMap[size] || 24;

  return (
    <div className="loading-spinner-container" role="status" aria-live="polite">
      <svg
        className="loading-spinner"
        width={px}
        height={px}
        viewBox="0 0 24 24"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true"
      >
        <circle
          className="spinner-track"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          strokeWidth="3"
          strokeOpacity="0.2"
        />
        <path
          className="spinner-head"
          d="M12 2a10 10 0 0 1 10 10"
          stroke="currentColor"
          strokeWidth="3"
          strokeLinecap="round"
        />
      </svg>
      {message && <span className="loading-spinner-label">{message}</span>}
    </div>
  );
};
