// src/components/ProfileDropdown.jsx
import React, { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { User, LogOut, Shield, Wallet } from './icons/Icons.jsx';

const cn = (...classes) => classes.filter(Boolean).join(' ');

export default function ProfileDropdown({ user, signOutUser }) {
    const [isOpen, setIsOpen] = useState(false);
    const dropdownRef = useRef(null);

    useEffect(() => {
        const handleClickOutside = (event) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target)) setIsOpen(false);
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    return (
        <div className="relative" ref={dropdownRef}>
            <button onClick={() => setIsOpen(p => !p)} className="flex items-center justify-center w-10 h-10 rounded-full bg-orange text-white font-bold text-lg">
                <User size={20} />
            </button>
            {isOpen && (
                <div className="absolute right-0 mt-2 w-64 premium-glass-menu rounded-lg shadow-xl z-50">
                    <div className="p-4 border-b border-white/10">
                        <p className="font-semibold text-white">{user?.displayName || 'User'}</p>
                        <p className="text-sm text-gray-300">{user?.email}</p>
                    </div>
                    <div className="py-1">
                        <Link to="/dashboard/profile" onClick={() => setIsOpen(false)} className="flex items-center w-full text-left px-4 py-2 text-sm text-gray-200 hover:bg-white/10 rounded-md">
                            <User size={16} className="mr-2" /> Profile
                        </Link>
                        <button onClick={() => alert("KYC Status: Verified (Placeholder)")} className="flex items-center w-full text-left px-4 py-2 text-sm text-gray-200 hover:bg-white/10 rounded-md">
                            <Shield size={16} className="mr-2" /> KYC Status
                        </button>
                        <button onClick={() => alert("Fund Wallet (Placeholder)")} className="flex items-center w-full text-left px-4 py-2 text-sm text-gray-200 hover:bg-white/10 rounded-md">
                            <Wallet size={16} className="mr-2" /> Fund Wallet
                        </button>
                    </div>
                    <div className="py-1 border-t border-white/10">
                        <button onClick={signOutUser} className="flex items-center w-full text-left px-4 py-2 text-sm text-gray-200 hover:bg-white/10 rounded-md">
                            <LogOut size={16} className="mr-2" /> Sign Out
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};