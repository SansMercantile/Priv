// src/pages/LoginPage.jsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/useAuth';
import { useEnvironment } from '../context/EnvironmentContext';
import { LogoIcon, Mail, Lock } from '../components/icons/Icons';

// Simple SVG icon components for the new buttons
const GoogleIcon = () => (
    <svg viewBox="0 0 24 24" className="w-5 h-5 mr-3">
        <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
        <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
        <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
        <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
    </svg>
);
const MicrosoftIcon = () => (
    <svg viewBox="0 0 24 24" className="w-5 h-5 mr-3">
        <path d="M11.5 22.5H2.5v-9H11.5v9zM22.5 22.5H13.5v-9H22.5v9zM11.5 11.5H2.5v-9H11.5v9zM22.5 11.5H13.5v-9H22.5v9z" fill="#F25022"/>
    </svg>
);


export default function LoginPage() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const navigate = useNavigate();
    const { signIn, signUp, authError, signInWithGoogle, signInWithMicrosoft } = useAuth();
    const { setDemoMode } = useEnvironment();

    const enterDemo = () => {
        setDemoMode(true);
        navigate('/dashboard');
    };

    const handleSignIn = (e) => {
        e.preventDefault();
        signIn(email, password);
    };

    const handleSignUp = (e) => {
        e.preventDefault();
        signUp(email, password);
    };

    return (
        <div className="flex items-center justify-center min-h-screen bg-silver font-sans">
            <div className="w-full max-w-md p-8 space-y-6 bg-white rounded-2xl shadow-xl">
                <div className="flex justify-center mb-4"><LogoIcon className="h-20 w-20"/></div>
                <div className="text-center">
                    <h1 className="text-4xl font-bold text-burgundy-black font-display">Sans Mercantile</h1>
                    <p className="mt-2 text-text-secondary">Welcome</p>
                </div>
                
                {authError && <p className="text-sm text-center text-accent-bad bg-red-100 p-3 rounded-lg">{authError}</p>}

                {/* --- Social Sign-in Buttons --- */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <button onClick={signInWithGoogle} className="flex items-center justify-center w-full py-3 font-semibold text-text-secondary bg-white border border-border-color rounded-lg hover:bg-gray-50 transition-colors">
                        <GoogleIcon />
                        Sign in with Google
                    </button>
                    <button onClick={signInWithMicrosoft} className="flex items-center justify-center w-full py-3 font-semibold text-text-secondary bg-white border border-border-color rounded-lg hover:bg-gray-50 transition-colors">
                        <MicrosoftIcon />
                        Sign in with Microsoft
                    </button>
                </div>

                <div className="relative flex py-4 items-center">
                    <div className="flex-grow border-t border-border-color"></div>
                    <span className="flex-shrink mx-4 text-text-secondary text-sm">Or with email</span>
                    <div className="flex-grow border-t border-border-color"></div>
                </div>

                {/* --- Email/Password Form --- */}
                <form className="space-y-4">
                    <div className="relative">
                        <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-text-secondary" size={20} />
                        <input type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} required className="w-full pl-10 pr-3 py-3 bg-input-bg rounded-lg border border-border-color focus:outline-none focus:ring-2 focus:ring-orange" />
                    </div>
                    <div className="relative">
                        <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-text-secondary" size={20} />
                        <input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} required className="w-full pl-10 pr-3 py-3 bg-input-bg rounded-lg border border-border-color focus:outline-none focus:ring-2 focus:ring-orange" />
                    </div>
                    <div className="flex flex-col space-y-3">
                        <button onClick={handleSignIn} className="w-full py-3 font-semibold text-white bg-burgundy-black rounded-lg hover:bg-crimson-noir transition-colors">Sign In</button>
                        <button onClick={handleSignUp} className="w-full py-3 font-semibold text-burgundy-black bg-transparent border-2 border-burgundy-black rounded-lg hover:bg-silver transition-colors">Sign Up</button>
                    </div>
                </form>

                <div className="pt-4 border-t border-border-color text-center">
                    <button
                        type="button"
                        onClick={enterDemo}
                        className="text-sm text-orange-600 font-semibold hover:underline"
                    >
                        Explore demo environment (no account required)
                    </button>
                </div>
            </div>
        </div>
    );
};