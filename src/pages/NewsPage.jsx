import React from 'react';
import News from '../components/News';

export default function NewsPage(){
    return (
        <div className="p-6">
            <h1 className="text-2xl font-bold mb-4">News & Feeds</h1>
            <News />
        </div>
    );
}
