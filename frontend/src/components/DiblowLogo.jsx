import React from 'react';

const DiblowLogo = ({ className = '', size = 'md' }) => {
  const sizes = {
    sm: { width: 32, height: 32, text: 'text-lg' },
    md: { width: 40, height: 40, text: 'text-xl' },
    lg: { width: 56, height: 56, text: 'text-2xl' },
  };
  const { width, height, text } = sizes[size] || sizes.md;

  return (
    <div className={`flex items-center gap-2.5 ${className}`}>
      <div className="relative flex items-center justify-center" style={{ width, height }}>
        <svg viewBox="0 0 100 100" className="w-full h-full" fill="none" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <linearGradient id="spiderGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#8B5CF6" />
              <stop offset="50%" stopColor="#A855F7" />
              <stop offset="100%" stopColor="#7C3AED" />
            </linearGradient>
            <filter id="glow">
              <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
              <feMerge><feMergeNode in="coloredBlur"/><feMergeNode in="SourceGraphic"/></feMerge>
            </filter>
          </defs>
          <path d="M50 15 L55 25 L70 10 L65 30 L85 20 L70 40 L90 45 L70 50 L90 55 L70 60 L85 80 L65 70 L70 90 L55 75 L50 85 L45 75 L30 90 L35 70 L15 80 L30 60 L10 55 L30 50 L10 45 L30 40 L15 20 L35 30 L30 10 L45 25 L50 15Z"
            fill="url(#spiderGrad)" filter="url(#glow)" stroke="#1a1a2e" strokeWidth="2" />
          <circle cx="45" cy="45" r="3" fill="#fff" opacity="0.9" />
          <circle cx="55" cy="45" r="3" fill="#fff" opacity="0.9" />
        </svg>
        <div className="absolute inset-0 bg-purple-500/20 blur-xl rounded-full" />
      </div>
      <div className="flex flex-col">
        <span className={`font-black ${text} tracking-tight font-heading`}>
          <span className="text-white">DIBLOW</span>
          <span className="bg-gradient-to-r from-purple-400 via-violet-500 to-purple-600 bg-clip-text text-transparent">CLOUD</span>
        </span>
        <span className="text-[9px] text-purple-400/60 tracking-[0.25em] uppercase -mt-0.5">Email Checker</span>
      </div>
    </div>
  );
};

export default DiblowLogo;
